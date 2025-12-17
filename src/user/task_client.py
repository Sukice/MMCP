from src.common.models import Task
from src.mcp_server.task_manager import init_task


def submit_task(task):
    init_task(task)
    pass


def add_task(
        task_name:str,
        model:str,
        task_content:str,
        file_path:str=None,
        available_tools=None,
):
    task = Task(task_name, model, task_content, available_tools, file_path)
    try:
        if submit_task(task):
            print("Success")
    except Exception as e:
        print(f"Submit Wrong:{e}")
    return


