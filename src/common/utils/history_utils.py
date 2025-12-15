import json
import os
from src.common.models import Task
from src.config.settings import TASK_HISTORY_FILE

def write_task_history(task: Task) -> None:
    """写入任务历史到文件（标准 JSON 数组格式）"""
    task_dict = task.to_dict()
    history_list = []
    if not os.path.exists(TASK_HISTORY_FILE):
        with open(TASK_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write('[]')

    # 1. 尝试读取现有文件内容
    if os.path.exists(TASK_HISTORY_FILE):
        try:
            with open(TASK_HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    history_list = json.loads(content)
                    # 确保读取出来的是列表
                    if not isinstance(history_list, list):
                        history_list = [history_list]
        except json.JSONDecodeError:
            # 如果现有文件格式错误（比如是你之前的 JSON Lines 格式），
            # 这里可以选择报错，或者尝试手动修复读取（见下文提示）
            print(f"警告：{TASK_HISTORY_FILE} 格式不正确，将初始化为新列表")
            history_list = []
        except Exception as e:
            print(f"读取历史文件失败：{e}")
            return

    # 2. 追加新任务
    history_list.append(task_dict)

    # 3. 覆盖写入整个列表
    try:
        with open(TASK_HISTORY_FILE, "w", encoding="utf-8") as f:
            # indent=2 或 4 可以让文件对人类可读（有缩进和换行）
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写入任务历史失败：{e}")