import requests
import json
url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Content-Type": "application/json"
}
data = {
    "model": "/model",
    "messages": [
        {
            "role": "user",
            "content": "say hi"
        }
    ]
}

response = requests.post(url, headers=headers, data=json.dumps(data))