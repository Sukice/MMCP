import os
import json

# 任务核心配置
MAX_COUNT = 50
SESSION_MAX_SIZE = 50
MAX_HANDLING_TASKS = 4
TASK_HISTORY_FILE = "task_history.json"
MODELS_CONFIG_FILE = "models_config.json"

# 默认配置
_DEFAULT_CONFIG = {}

def load_model_config():
    if os.path.exists(MODELS_CONFIG_FILE):
        try:
            with open(MODELS_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载模型配置失败: {e}")
    return _DEFAULT_CONFIG


# 初始化全局变量
_config_data = load_model_config()
DEFAULT_MODELS = _config_data["models"]
API_KEYS = _config_data["api_keys"]
BASE_URL = _config_data["base_urls"]


def _save_to_file():
    """内部辅助函数：保存当前内存配置到文件"""
    data_to_save = {
        "models": DEFAULT_MODELS,
        "api_keys": API_KEYS,
        "base_urls": BASE_URL
    }
    try:
        with open(MODELS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"写入配置文件失败: {e}")
        return False


def save_model_config(name: str, base_url: str, api_key: str):
    """添加/更新模型配置"""
    if name not in DEFAULT_MODELS:
        DEFAULT_MODELS.append(name)
    API_KEYS[name] = api_key
    BASE_URL[name] = base_url
    return _save_to_file()


def delete_model_config(name: str):
    """[新增] 删除模型配置"""
    if name in DEFAULT_MODELS:
        DEFAULT_MODELS.remove(name)

    # 移除字典中的键（如果存在）
    API_KEYS.pop(name, None)
    BASE_URL.pop(name, None)

    print(f"模型 {name} 已从配置中移除")
    return _save_to_file()


def get_api_key(model_name: str) -> str:
    return API_KEYS.get(model_name, "")


def get_base_url(model_name: str) -> str:
    return BASE_URL.get(model_name, "")