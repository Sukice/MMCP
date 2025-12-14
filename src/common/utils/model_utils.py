from openai import OpenAI


def get_openai_client(model_name: str) -> OpenAI:
    model = OpenAI(
        api_key='DEEPSEEK_API_KEY',
        base_url='DEEPSEEK_BASE_URL',
    )
    return model