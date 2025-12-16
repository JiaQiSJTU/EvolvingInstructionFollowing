# encoding = "utf-8"
from openai import OpenAI


def LLM_backend(api_key, messages, model_name, base_url, temperature=1.0, use_json_mode=True):

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    if use_json_mode:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}
            # "json_mode"= True
        )
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            # response_format={"type": "json_object"}
            # "json_mode"= True
        )

    return response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens


def load_jsonl(path: str):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines.append(json.loads(line))
    return lines


def write_jsonl(path: str, records):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
