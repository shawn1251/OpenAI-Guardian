from mitmproxy import http
import requests
import json

is_blocked = False

def request(flow: http.HTTPFlow) -> None:
    global is_blocked
    if "api.openai.com" in flow.request.pretty_url:
        print("======request======")
        print("Request URL:", flow.request.pretty_url)
        print("Request Headers:", flow.request.headers)
        request_body = flow.request.text
        print("Request Body:", request_body)
        try:
            data = json.loads(request_body)
            content = data['messages']
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print("Error parsing request body:", e)
    
        # Send the request body to guardian service
        response = requests.post("http://guardian:8000/", json={
            "content": content})
        
        guardian_response = response.json()
        print("Guardian Response:", guardian_response)
        if guardian_response.get('label') == True:
            flow.response = http.Response.make(
                403,
                guardian_response.get("message").encode(),
                {"Content-Type": "text/plain"}
            )
            is_blocked = True



def response(flow: http.HTTPFlow) -> None:
    global is_blocked
    if "api.openai.com" in flow.request.pretty_url:
        if is_blocked:
            is_blocked = False
            return
        print("======response======")
        print("Response Status Code:", flow.response.status_code)
        print("Response Headers:", flow.response.headers)
        response_body = flow.response.text
        print("Response Body:", response_body)
        try:
            data = json.loads(response_body)
            response_content = data['choices'][0]['message']
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print("Error parsing request body:", e)
    
        # this granit guardian service need both user and assistant message
        request_body = flow.request.text
        print("Request Body:", request_body)
        try:
            data = json.loads(request_body)
            request_content = data['messages'][0]
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print("Error parsing request body:", e)

        full_content = [request_content, response_content]
        print("Full conversation", full_content)
        # Send the "user" + "assistant" message to guardian service
        response = requests.post("http://guardian:8000/", json={
            "content": full_content})
        
        guardian_response = response.json()
        print("Guardian Response:", guardian_response)
        if guardian_response.get('label') == True:
            flow.response = http.Response.make(
                403,
                guardian_response.get("message").encode(),
                {"Content-Type": "text/plain"}
            )
        
