import os


def chatgpt_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Set it in GitHub Actions secrets or your local environment."
        )
    return key


def deepseek_api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY environment variable is not set. "
            "Set it in GitHub Actions secrets or your local environment."
        )
    return key
