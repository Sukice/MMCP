from typing import Dict, Optional, List
from src.common.models import Model
from src.config.settings import DEFAULT_MODELS

# 全局模型池
# Key: 模型名称 (str), Value: Model 对象
_model_pool: Dict[str, Model] = {}


def init_model(model_name: str) -> Model:
    """动态添加/初始化单个模型到内存池"""
    # 如果已存在，直接返回，避免重置状态
    if model_name in _model_pool:
        return _model_pool[model_name]

    # 根据你提供的 Model 定义，这里不需要传 api_key
    model = Model(name=model_name)
    _model_pool[model_name] = model
    print(f"已初始化模型: {model_name}")
    return model


def init_default_models() -> None:
    """初始化默认模型池 (启动时调用)"""
    global _model_pool
    # 启动时可以清空旧状态
    _model_pool = {}
    for model_name in DEFAULT_MODELS:
        init_model(model_name)
    print(f"当前模型池列表: {list(_model_pool.keys())}")


def get_model(model_name: str) -> Optional[Model]:
    """获取模型实例"""
    return _model_pool.get(model_name)


def list_models() -> List[Model]:
    """列出所有模型对象"""
    # 因为 _model_pool 是字典，所以这里用 .values() 是安全的
    return list(_model_pool.values())


def remove_model(model_name: str):
    """[核心修复] 从内存池中移除模型"""
    global _model_pool

    # 必须使用字典的删除方式，不能用列表推导式
    if model_name in _model_pool:
        del _model_pool[model_name]
        print(f"已从内存移除模型: {model_name}")
    else:
        print(f"尝试移除模型 {model_name} 失败: 内存池中未找到")


# --- 状态管理辅助函数 ---

def update_model_state(model_name: str, state: str) -> None:
    """更新模型状态"""
    model = get_model(model_name)
    if model:
        try:
            model.state = state
        except ValueError as e:
            print(f"状态更新失败: {e}")


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