from openai import OpenAI
from llm_models_api import config

_CHATGPT_API_KEY = config.chatgpt_api_key()
_CLIENT = OpenAI(api_key=_CHATGPT_API_KEY)

def get_response_from_chatgpt(system_role: str, prompt_list: list[str], model: str = "gpt-5-nano-2025-08-07"):
    if len(prompt_list) == 0:
        raise ValueError("message_list should have at least 1 elements, system role and user prompt")

    message_list = [{"role": "system", "content": system_role}]
    for prompt in prompt_list:
        message_list.append({"role": "user", "content": prompt})

    response = _CLIENT.chat.completions.create(
        model=model,
        store=False,
        messages=message_list,
        stream=False
    )
    return response.choices[0].message.content
