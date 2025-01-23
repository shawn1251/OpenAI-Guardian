from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import yaml

def read_config():
    with open('./config.yml', 'r') as file:
        config = yaml.safe_load(file)
    return config

config = read_config()
api_key = config.get('API_KEY')
mitmproxy = config.get('MITMPROXY')

openai_client = OpenAI(api_key = api_key, base_url=mitmproxy)


app = FastAPI()


class Message(BaseModel):
    content: str = "answer me hello"

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/")
def chat(message: Message):
    content = message.content
    try:
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
    except Exception as e:
        return {"error": f"{e}"}
