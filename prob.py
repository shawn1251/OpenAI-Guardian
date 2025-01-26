import math

# Define safe and risky tokens
safe_token = "No"
risky_token = "Yes"

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
# Test the function with a sample response
response = {
    'id': 'chatcmpl-698deaf81e254147be04db54d07c140c',
    'object': 'chat.completion',
    'created': 1737873712,
    'model': '/model',
    'choices': [{
        'index': 0,
        'message': {
            'role': 'assistant',
            'content': 'Yes',
            'tool_calls': []
        },
        'logprobs': {
            'content': [{
                'token': 'Yes',
                'logprob': -0.08035564422607422,
                'bytes': [89, 101, 115],
                'top_logprobs': [
                    {'token': 'Yes', 'logprob': -0.08035564422607422, 'bytes': [89, 101, 115]},
                    {'token': 'No', 'logprob': -2.564730644226074, 'bytes': [78, 111]},
                    {'token': ' Yes', 'logprob': -10.361605644226074, 'bytes': [32, 89, 101, 115]},
                    {'token': 'yes', 'logprob': -10.713168144226074, 'bytes': [121, 101, 115]},
                    {'token': 'To', 'logprob': -11.486605644226074, 'bytes': [84, 111]}
                ]
            }, {
                'token': '',
                'logprob': -8.189342770492658e-05,
                'bytes': [],
                'top_logprobs': [
                    {'token': '', 'logprob': -8.189342770492658e-05, 'bytes': []},
                    {'token': '\n\n\n', 'logprob': -11.363363265991211, 'bytes': [10, 10, 10]},
                    {'token': '\n\n', 'logprob': -11.746175765991211, 'bytes': [10, 10]},
                    {'token': '\n', 'logprob': -13.117269515991211, 'bytes': [10]},
                    {'token': '">', 'logprob': -13.261800765991211, 'bytes': [34, 62]}
                ]
            }]
        },
        'finish_reason': 'stop',
        'stop_reason': None
    }],
    'usage': {
        'prompt_tokens': 126,
        'total_tokens': 128,
        'completion_tokens': 2,
        'prompt_tokens_details': None
    },
    'prompt_logprobs': None
}

# Parse the response and print the results
label, prob_of_risk = parse_output(response)
print(f"Label: {label}, Probability of Risk: {prob_of_risk}")