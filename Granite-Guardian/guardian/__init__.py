import math
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


safe_token = "No"
unsafe_token = "Yes"
nlogprobs = 20

def parse_output(output, input_len):
    label, prob_of_risk = None, None

    if nlogprobs > 0:

        list_index_logprobs_i = [torch.topk(token_i, k=nlogprobs, largest=True, sorted=True)
                                 for token_i in list(output.scores)[:-1]]
        if list_index_logprobs_i is not None:
            prob = get_probabilities(list_index_logprobs_i)
            prob_of_risk = prob[1]

    res = tokenizer.decode(output.sequences[:,input_len:][0],skip_special_tokens=True).strip()
    if unsafe_token.lower() == res.lower():
        label = unsafe_token
    elif safe_token.lower() == res.lower():
        label = safe_token
    else:
        label = "Failed"

    return label, prob_of_risk.item()

def get_probabilities(logprobs):
    safe_token_prob = 1e-50
    unsafe_token_prob = 1e-50
    for gen_token_i in logprobs:
        for logprob, index in zip(gen_token_i.values.tolist()[0], gen_token_i.indices.tolist()[0]):
            decoded_token = tokenizer.convert_ids_to_tokens(index)
            if decoded_token.strip().lower() == safe_token.lower():
                safe_token_prob += math.exp(logprob)
            if decoded_token.strip().lower() == unsafe_token.lower():
                unsafe_token_prob += math.exp(logprob)

    probabilities = torch.softmax(
        torch.tensor([math.log(safe_token_prob), math.log(unsafe_token_prob)]), dim=0
    )

    return probabilities

#model_path = "ibm-granite/granite-guardian-3.0-2b"
model_path = "./model"

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype=torch.bfloat16
)
tokenizer = AutoTokenizer.from_pretrained(model_path)

def detect_risks(messages):
    # change string to boolean
    label_map = {
        "No": False,
        "Yes": True
    }
    # Check "harm" risk first
    guardian_config = {"risk_name": "harm"}
    results = {}
    input_ids = tokenizer.apply_chat_template(
        messages, guardian_config=guardian_config, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)
    input_len = input_ids.shape[1]

    model.eval()

    with torch.no_grad():
        output = model.generate(
            input_ids,
            do_sample=False,
            max_new_tokens=20,
            return_dict_in_generate=True,
            output_scores=True,
        )

    label, prob_of_risk = parse_output(output, input_len)
    label = label_map[label]
    results["harm"] = {
        "label": label,
        "prob": prob_of_risk
    }
    if not label:
        # If "harm" is not detected, return empty dictionary
        return {}
    else:
        # Check other risks if "harm" is detected
        other_risk_names = ["unethical_behavior", "sexual_content", "violence"]
        for risk_name in other_risk_names:
            guardian_config = {"risk_name": risk_name}
            input_ids = tokenizer.apply_chat_template(
                messages, guardian_config=guardian_config, add_generation_prompt=True, return_tensors="pt"
            ).to(model.device)
            input_len = input_ids.shape[1]

            with torch.no_grad():
                output = model.generate(
                    input_ids,
                    do_sample=False,
                    max_new_tokens=20,
                    return_dict_in_generate=True,
                    output_scores=True,
                )

            label, prob_of_risk = parse_output(output, input_len)
            results[risk_name] = {
                "label": label_map[label],
                "prob": prob_of_risk
            }
        return results