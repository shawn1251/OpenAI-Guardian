from mitmproxy import http
import requests
import json
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

is_blocked = False

def request(flow: http.HTTPFlow) -> None:
    global is_blocked
    if "api.openai.com" in flow.request.pretty_url:
        logger.info("======request======")
        logger.info("Request URL: %s", flow.request.pretty_url)
        logger.info("Request Headers: %s", flow.request.headers)
        request_body = flow.request.text
        logger.info("Request Body: %s", request_body)

        url = "http://guardian:8000/v1/chat/completions"
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

        logger.info("Guardian Response: %s", response.json())
        flow.response = http.Response.make(
                403,
                response.get("message").encode(),
                {"Content-Type": "text/plain"}
            )
        # except (json.JSONDecodeError, KeyError, IndexError) as e:
        #     logger.error("Error parsing request body: %s", e)
    
        # # Send the request body to guardian service
        # response = requests.post("http://guardian:8000/", json={
        #     "content": content})
        
        # guardian_response = response.json()
        # logger.info("Guardian Response: %s", guardian_response)
        # if guardian_response.get('label') == True:
        #     flow.response = http.Response.make(
        #         403,
        #         guardian_response.get("message").encode(),
        #         {"Content-Type": "text/plain"}
        #     )
        #     is_blocked = True

def response(flow: http.HTTPFlow) -> None:
    global is_blocked
    if "api.openai.com" in flow.request.pretty_url:
        if is_blocked:
            is_blocked = False
            return
        logger.info("======response======")
        logger.info("Response Status Code: %s", flow.response.status_code)
        logger.info("Response Headers: %s", flow.response.headers)
        response_body = flow.response.text
        logger.info("Response Body: %s", response_body)
        # try:
        #     data = json.loads(response_body)
        #     response_content = data['choices'][0]['message']
        # except (json.JSONDecodeError, KeyError, IndexError) as e:
        #     logger.error("Error parsing request body: %s", e)
    
        # # this granit guardian service need both user and assistant message
        # request_body = flow.request.text
        # logger.info("Request Body: %s", request_body)
        # try:
        #     data = json.loads(request_body)
        #     request_content = data['messages'][0]
        # except (json.JSONDecodeError, KeyError, IndexError) as e:
        #     logger.error("Error parsing request body: %s", e)

        # full_content = [request_content, response_content]
        # logger.info("Full conversation: %s", full_content)
        # # Send the "user" + "assistant" message to guardian service
        # response = requests.post("http://guardian:8000/", json={
        #     "content": full_content})
        
        # guardian_response = response.json()
        # logger.info("Guardian Response: %s", guardian_response)
        # if guardian_response.get('label') == True:
        #     flow.response = http.Response.make(
        #         403,
        #         guardian_response.get("message").encode(),
        #         {"Content-Type": "text/plain"}
        #     )
