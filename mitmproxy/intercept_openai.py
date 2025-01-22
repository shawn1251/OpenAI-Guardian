from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    if "api.openai.com" in flow.request.pretty_url:
        print("Request URL:", flow.request.pretty_url)
        print("Request Headers:", flow.request.headers)
        print("Request Body:", flow.request.text)


def response(flow: http.HTTPFlow) -> None:
    if "api.openai.com" in flow.request.pretty_url:
        print("Response Status Code:", flow.response.status_code)
        print("Response Headers:", flow.response.headers)
        print("Response Body:", flow.response.text)
