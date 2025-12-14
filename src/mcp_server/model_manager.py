from typing import Dict, Optional, List
from src.common.models import Model
from src.config.settings import DEFAULT_MODELS

# 全局模型池
_model_pool: Dict[str, Model] = {}


def init_model(model_name: str) -> Model:
    """初始化单个模型"""
    if model_name in _model_pool:
        return _model_pool[model_name]
    model = Model(name=model_name)
    _model_pool[model_name] = model
    return model


def init_default_models() -> None:
    """初始化默认模型池"""
    for model_name in DEFAULT_MODELS:
        init_model(model_name)


def get_model(model_name: str) -> Optional[Model]:
    """获取模型实例"""
    return _model_pool.get(model_name)


def list_models() -> List[Model]:
    """列出所有模型"""
    return list(_model_pool.values())


def update_model_state(model_name: str, state: str) -> None:
    """更新模型状态"""
    model = get_model(model_name)
    if model:
        model.state = state


def bind_model_task(model_name: str, task_id: str, task_name: str) -> None:
    """绑定模型到任务"""
    model = get_model(model_name)
    if model:
        model.bind_task(task_id, task_name)


def unbind_model_task(model_name: str) -> None:
    """解绑模型任务"""
    model = get_model(model_name)
    if model:
        model.unbind_task()