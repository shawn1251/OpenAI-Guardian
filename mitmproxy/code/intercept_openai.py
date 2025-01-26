from mitmproxy import http
import requests
import json
import logging
import math

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define safe and risky tokens
safe_token = "No"
risky_token = "Yes"

# Define risk types and their corresponding explanations
RISK_TYPES = {
    "harm": "The prompt is considered toxic.",
    # "unethical_behavior": "Inquiries on how to perform an illegal activity",
    # "sexual_content": "Any sexual content",
    # "violence": "Description of violent acts"
}

def parse_output(response):
    """
    Parse the model response to extract the label and probability of risk.

    Args:
        response (dict): The model response containing logprobs and generated text.

    Returns:
        label (str): The predicted label ("Yes", "No", or "Failed").
        prob_of_risk (float): The probability of the risky token.
    """
    label, prob_of_risk = None, None

    # Extract logprobs from the response
    logprobs = response['choices'][0]['logprobs']['content']

    if logprobs:
        # Calculate probabilities based on logprobs
        prob = get_probabilities(logprobs)
        prob_of_risk = prob[1]

    # Extract the generated text from the response
    res = response['choices'][0]['message']['content'].strip()
    if risky_token.lower() == res.lower():
        label = risky_token
    elif safe_token.lower() == res.lower():
        label = safe_token
    else:
        label = "Failed"

    return label, prob_of_risk

def get_probabilities(logprobs):
    """
    Calculate the probabilities of safe and risky tokens based on logprobs.

    Args:
        logprobs (list): A list of token data containing logprobs and top_logprobs.

    Returns:
        probabilities (list): A list containing the probabilities of safe and risky tokens.
    """
    safe_token_prob = 1e-50  # Initialize with a small value to avoid log(0)
    risky_token_prob = 1e-50  # Initialize with a small value to avoid log(0)

    for token_data in logprobs:
        # Check each candidate token in top_logprobs
        for top_logprob in token_data['top_logprobs']:
            token = top_logprob['token'].strip().lower()
            logprob = top_logprob['logprob']

            # Accumulate probabilities for safe and risky tokens
            if token == safe_token.lower():
                safe_token_prob += math.exp(logprob)
            elif token == risky_token.lower():
                risky_token_prob += math.exp(logprob)

    # Calculate softmax manually
    log_safe = math.log(safe_token_prob)
    log_risky = math.log(risky_token_prob)
    max_log = max(log_safe, log_risky)  # For numerical stability

    # Compute softmax
    exp_safe = math.exp(log_safe - max_log)
    exp_risky = math.exp(log_risky - max_log)
    total = exp_safe + exp_risky

    safe_prob = exp_safe / total
    risky_prob = exp_risky / total

    return [safe_prob, risky_prob]

def send_to_guardian(messages, risk_name="harm"):
    """
    Send the request to the Guardian model for analysis.

    Args:
        messages (list): The list of messages to be sent to the Guardian model.
        risk_name (str): The type of risk to analyze (default is "harm").

    Returns:
        guardian_response (dict): The response from the Guardian model.
    """
    url = "http://guardian:8000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "/model",
        "messages": messages,
        "chat_template_kwargs": {
            "guardian_config": {
                "risk_name": risk_name,
            }
        },
        "logprobs": True,
        "top_logprobs": 5,
    }

    # Send the request to the Guardian model
    guardian_response = requests.post(url, headers=headers, data=json.dumps(data))
    return guardian_response.json()

def detect_risks(messages):
    """
    Detect risks in the messages by checking multiple risk types.

    Args:
        messages (list): The list of messages to analyze.

    Returns:
        results (dict): A dictionary containing the results for each risk type.
    """
    results = {}

    # Check each risk type
    for risk_name in RISK_TYPES.keys():
        guardian_response = send_to_guardian(messages, risk_name)
        logger.info(f">>>guardian >> {guardian_response}")
        label, prob_of_risk = parse_output(guardian_response)
        results[risk_name] = {
            "label": label == risky_token,
            "prob": prob_of_risk
        }

    return results

def generate_error_message(detect_result):
    """
    Generate an error message based on the detected risks.

    Args:
        detect_result (dict): The results of the risk detection.

    Returns:
        error_message (str): The generated error message.
    """
    error_message = "The prompt was blocked because it contained:\n"
    has_risk = False

    # Check each risk type and append to the error message if detected
    for risk_name, explanation in RISK_TYPES.items():
        if risk_name == "harm": continue # this is general category
        if detect_result.get(risk_name, {}).get("label", False):
            error_message += f"{explanation}\n"
            has_risk = True

    if not has_risk:
        error_message = "No specific risks detected, but the prompt is considered harmful."

    return error_message

def log_request(flow: http.HTTPFlow):
    """
    Log the request details.

    Args:
        flow (http.HTTPFlow): The intercepted HTTP flow.
    """
    logger.info("====== Request ======")
    logger.info("Request URL: %s", flow.request.pretty_url)
    logger.info("Request Headers: %s", flow.request.headers)
    logger.info("Request Body: %s", json.loads(flow.request.text))

def log_response(flow: http.HTTPFlow):
    """
    Log the response details.

    Args:
        flow (http.HTTPFlow): The intercepted HTTP flow.
    """
    logger.info("====== Response ======")
    logger.info("Response Status Code: %s", flow.response.status_code)
    logger.info("Response Headers: %s", flow.response.headers)
    logger.info("Response Body: %s", json.loads(flow.response.text))

def request(flow: http.HTTPFlow) -> None:
    """
    Intercept requests to OpenAI API and forward them to the Guardian model for analysis.
    Block the request if the Guardian model detects a risky response.

    Args:
        flow (http.HTTPFlow): The intercepted HTTP flow.
    """
    if "api.openai.com" in flow.request.pretty_url:
        # Log the request details
        log_request(flow)

        # Parse the request body
        request_body = json.loads(flow.request.text)

        # Detect risks in the request messages
        detect_result = detect_risks(request_body["messages"])
        logger.info("Risk Detection Results: %s", detect_result)

        # Generate error message if risks are detected
        if any(result["label"] for result in detect_result.values()):
            error_message = generate_error_message(detect_result)
            logger.warning("Risky content detected! Blocking request.")
            flow.response = http.Response.make(
                403,  # Forbidden status code
                json.dumps({"error": error_message}),
                {"Content-Type": "application/json"}
            )

def response(flow: http.HTTPFlow) -> None:
    """
    Intercept responses from OpenAI API and forward them to the Guardian model for analysis.
    Block the response if the Guardian model detects a risky response.

    Args:
        flow (http.HTTPFlow): The intercepted HTTP flow.
    """
    if "api.openai.com" in flow.request.pretty_url:
        # Log the response details
        log_response(flow)

        # Parse the response body
        response_body = json.loads(flow.response.text)

        # Extract the assistant's message from the response
        assistant_message = response_body["choices"][0]["message"]["content"]

        #IMPORTANT: role: user message is necessary
        request_body = json.loads(flow.request.text)
        messages = request_body["messages"]

        # Extend and rap the assistant's message in the same format as the request
        messages.append({"role": "assistant", "content": assistant_message})
        # Detect risks in the response messages
        detect_result = detect_risks(messages)
        logger.info("Risk Detection Results: %s", detect_result)


        # Generate error message if risks are detected
        if any(result["label"] for result in detect_result.values()):
            error_message = generate_error_message(detect_result)
            logger.warning("Risky content detected! Blocking response.")
            flow.response = http.Response.make(
                403,  # Forbidden status code
                json.dumps({"error": error_message}),
                {"Content-Type": "application/json"}
            )

        