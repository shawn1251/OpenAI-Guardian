# OPENAI-Guardian

This project implements intercepting conversations with OpenAI using mitmproxy and blocking harmful content using IBM Granite Guardian.

## Introduction
### GPU Support Issue
The author's GPU is Pascal architecture, which is not supported by vllm. Initially, a model wrapped with FastAPI and transformers was used, but it made the project too complex and low quality. The current version integrates vllm and builds a CPU model in Docker Compose. A GPU version will be added after testing in a better environment.

### Model Downgrade
Due to hardware limitations, the latest 3.1-2b model exceeds the author's environment capacity. Currently using 3.0-2b.

### SSL
The author did not purchase a domain and IP. For the experimental setup, a self-signed SSL is used.
1. Create cert
```bash
mkdir certs
cd certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mykey.key -out mycert.crt
```
2. Replace in `docker-compose.yml` conf
```docker
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      #- ./nginx.without_SSL.conf:/etc/nginx/conf.d/default.conf
      - ./certs:/etc/nginx/certs 
```
3. Change `http://127.0.0.1/v1` to `https://127.0.0.1/v1` in `config.yml`
4. Refer to [this post](https://community.openai.com/t/ssl-certificate-verify-failed-certificate-verify-failed-self-signed-certificate-in-certificate-chain/705003/11) to disable certificate verification in `chat.py`
```python
client = OpenAI(
    http_client = httpx.Client(verify=False)
)
```
### Multiple Harmful Types Detection
Currently, multiple harmful types detection is desired, but due to slow local environment, OpenAI server closes connection during intercept. No solution yet. Future improvements in detection efficiency will allow uncommenting in `intercept_openai.py`
```python
# Define risk types and their corresponding explanations
RISK_TYPES = {
    "harm": "The prompt is considered toxic.",
    # "unethical_behavior": "Inquiries on how to perform an illegal activity",
    # "sexual_content": "Any sexual content",
    # "violence": "Description of violent acts"
}
```

## Requirements
* git
* docker
* docker-compose
* huggingface-cli
* python 3.12
    * openai
    * yaml

## Preparation
1. Download Granite Guardian model
Use [huggingface-cli](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli) to download ibm-granite/granite-guardian-3.0-2b.
    `huggingface-cli download ibm-granite/granite-guardian-3.0-2b --local-dir model`
2. Increase swap
    Due to the large model size, increase swap to the maximum for CPU execution. The author's M1 Pro environment requires 16G memory for Docker to run the 3.0-2b model. The 3.1-2b model still causes OOM.

3. Clone vllm project
Run `git clone https://github.com/vllm-project/vllm.git`. Build the CPU version of vllm Docker as needed. Modify the settings in docker-compose.yml according to your CPU.
```
  guardian:
    build:
      context: ./vllm # need .git folder for setuptools-scm
      #dockerfile: ./Dockerfile.cpu # x86 cpu image
      dockerfile: ./Dockerfile.arm #for apple silicon
```
## Installation
* `docker-compose build`
* `mv config.example.yml config.yml` and fill in the API KEY 
## Usage
* `docker-compose up -d`
* Use `chat.py` with prepared messages to test
    * `python chat.py --message normal`
    * `python chat.py --message harm`
    * `python chat.py --message unethical`
    * `python chat.py --message sexual`
    * `python chat.py --message violence`
### Example
#### Normal
```!
python chat.py --message normal
INFO:__main__:Client init.
INFO:__main__:Message: {'role': 'user', 'content': 'Normal message: Hello, how are you?'}
INFO:httpx:HTTP Request: POST https://127.0.0.1/v1/chat/completions "HTTP/1.1 200 OK"
Chat response: ChatCompletion(id='chatcmpl-Au3HKvYYTKZYj5R45OLK5oSTBKhe6', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content="Hello! I'm doing well, thank you. How about you?", refusal=None, role='assistant', audio=None, function_call=None, tool_calls=None))], created=1737922334, model='gpt-4o-mini-2024-07-18', object='chat.completion', service_tier='default', system_fingerprint='fp_72ed7ab54c', usage=CompletionUsage(completion_tokens=14, prompt_tokens=16, total_tokens=30, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))
```
#### Harm
```!
python chat.py --message harm  
INFO:__main__:Client init.
INFO:__main__:Message: {'role': 'user', 'content': 'what the fuck'}
INFO:httpx:HTTP Request: POST https://127.0.0.1/v1/chat/completions "HTTP/1.1 403 Forbidden"
Error code: 403 - {'error': 'No specific risks detected, but the prompt is considered harmful.'}
```


## Acknowledgments

- mitmproxy for providing the interception capabilities.
- IBM Granite Guardian for content evaluation.