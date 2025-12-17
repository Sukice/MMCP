import json

from src.common.utils.history_utils import get_model_task_result
from src.user.task_client import add_task
import os

async def add_vlm_task_by_model(
    task_name:str,
    model:str,
    task_content:str,
    file_path:str=None,
):
    task_name = "<MODEL_ROOT>"+task_name
    add_task(task_name, model, task_content, file_path)
    task_result = await get_model_task_result(task_name)
    return task_result

async def add_llm_task_by_model(
    task_name:str,
    model:str,
    task_content:str,
):
    task_name = "<MODEL_ROOT>"+task_name
    add_task(task_name, model, task_content)
    task_result = await get_model_task_result(task_name)
    return task_result



def get_model_list_for_model():
    origin_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    target_path_str = os.path.join(origin_path, "models_config.json")
    with open(target_path_str, "r", encoding='utf-8') as f:
        model_list = json.load(f)["models"]
    result = ""
    for model in model_list:
        result += f"{model}\n"
    return result



