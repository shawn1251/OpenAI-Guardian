from fastapi import FastAPI
from pydantic import BaseModel, Field
from guardian import detect_risks

app = FastAPI()

# Define the structure of a dialog message
class Dialog(BaseModel):
    role: str = "user"
    content: str = "I want to kill you"

# Define the structure of the incoming message payload
class Message(BaseModel):
    content: list[Dialog] = Field(
        example=[
            {"role": "user", "content": "Tell me a joke."},
            {"role": "assistant", "content": "Why did the chicken cross the road? To get to the other side!"}
        ]
    )

# Define the structure of the response
class DetectRes(BaseModel):
    label: bool
    message: str

@app.get("/")
def read_root():
    # Basic endpoint to check if the service is running
    return {"Hello": "World"}

@app.post("/", response_model=DetectRes)
def detect(messages: Message):
    print(messages)
    # Call the detect_risks function to analyze the messages
    detect_result = detect_risks(messages.content)
    print(detect_result)
    
    # If no risks are detected, return a response indicating no issues
    if len(detect_result) == 0:
        return DetectRes(label=False, message="")
    
    # Define explanations for different types of detected risks
    response_text = {
        "unethical_behavior": "Inquiries on how to perform an illegal activity",
        "sexual_content": "Any sexual content",
        "violence": "Description of violent acts"
    }
    
    label = False
    explain_message = "The prompt was blocked because it contained:\n"
    
    # Check for each type of risk and update the response accordingly
    for k in response_text:
        if detect_result[k]["label"]:
            label = True
            explain_message += f"{response_text[k]}\n"
    
    # Check for general harmful content if no specific risks were found
    if not label:
        if detect_result["harm"]["label"]:
            label = True
            explain_message = "The prompt is considered toxic."

    # Return the final detection result
    return DetectRes(label=label, message=explain_message)
