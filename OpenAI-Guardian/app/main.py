from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()


class Message(BaseModel):
    content: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chat")
def chat(message: Message):
    content = message.content
    return {"response": f"You said: {content}"}
