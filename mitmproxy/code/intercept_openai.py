from mitmproxy import http
import requests
import json

def request(flow: http.HTTPFlow) -> None:
    if "api.openai.com" in flow.request.pretty_url:
        #print("Request URL:", flow.request.pretty_url)
        #print("Request Headers:", flow.request.headers)
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
        print(guardian_response)
        if guardian_response.get('label') == True:
            flow.response = http.Response.make(
                403,
                guardian_response.get("message").encode(),
                {"Content-Type": "text/plain"}
            )



def response(flow: http.HTTPFlow) -> None:
    if "api.openai.com" in flow.request.pretty_url:
        print("Response Status Code:", flow.response.status_code)
        print("Response Headers:", flow.response.headers)
        print("Response Body:", flow.response.text)
