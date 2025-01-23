from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

app = FastAPI()


model_name_or_path = 'ibm-granite/granite-guardian-hap-38m' # choose the smaller model
model = AutoModelForSequenceClassification.from_pretrained(model_name_or_path)
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
def predict_toxicity(text):
    input = tokenizer(text, padding=True, truncation=True, return_tensors="pt")

    with torch.no_grad():
        logits = model(**input).logits
        prediction = torch.argmax(logits, dim=1).detach().numpy()
        probability = torch.softmax(logits, dim=1).detach().numpy()[:, 1]
    
    return prediction[0], probability[0]


class Message(BaseModel):
    content: str = "kill you kill you all"

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/")
def detect(message: Message):
    content = message.content
    prediction, probability = predict_toxicity(content)
    # model return numpy.int64 which cannot be encoded
    return {
        "prediction": int(prediction), 
        "probability": float(probability)
    }
