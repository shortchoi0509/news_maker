from openai import OpenAI
from llm_models_api import config

_DEEPSEEK_API_KEY = config.deepseek_api_key()
_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_CLIENT = OpenAI(api_key=_DEEPSEEK_API_KEY, base_url=_DEEPSEEK_BASE_URL)


def get_response_from_deepseek(system_role: str, prompt_list: list[str], model: str = "deepseek-chat"):
    if len(prompt_list) == 0:
        raise ValueError("message_list should have at least 1 elements, system role and user prompt")

    message_list = [{"role": "system", "content": system_role}]
    for prompt in prompt_list:
        message_list.append({"role": "user", "content": prompt})

    response = _CLIENT.chat.completions.create(
        model=model,
        messages=message_list,
        stream=False
    )
    return response.choices[0].message.content

