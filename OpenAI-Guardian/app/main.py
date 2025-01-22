from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import yaml

def read_config():
    with open('/home/shawn/OpenAI-Guardian/OpenAI-Guardian/config.yml', 'r') as file:
        config = yaml.safe_load(file)
    return config

config = read_config()
api_key = config.get('API_KEY')


openai_client = OpenAI(api_key = api_key)


app = FastAPI()


class Message(BaseModel):
    content: str = "answer me hello"

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chat")
def chat(message: Message):
    content = message.content
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            {"role": "user", "content": f"{content}"}
        ]
    )
    print(completion)
    response_text = completion.choices[0].message.content
    return {"response": f"{response_text}"}
