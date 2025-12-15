from openai import AsyncOpenAI

def get_openai_client(model_name: str):
    client = None
    if model_name == "deepseek-chat":
        client = AsyncOpenAI(
            api_key='sk-044217e5854b4507895ea787f175df87',
            base_url='https://api.deepseek.com',
            timeout=300.0,
        )
    return client