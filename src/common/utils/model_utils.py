from openai import AsyncOpenAI
from src.config.settings import get_api_key, get_base_url

def get_openai_client(model_name: str):
    """
    动态获取 OpenAI 客户端
    根据 settings.py 中的配置自动适配不同的模型
    """
    api_key = get_api_key(model_name)
    base_url = get_base_url(model_name)

    if not api_key or not base_url:
        print(f"Error: 模型 {model_name} 缺少 api_key 或 base_url 配置")
        return None

    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=300.0,
        )
        return client
    except Exception as e:
        print(f"创建模型客户端失败: {e}")
        return None