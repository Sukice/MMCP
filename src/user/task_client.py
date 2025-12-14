from src.common.models import Task
from src.mcp_server.task_manager import init_task


def submit_task(task):
    init_task(task)
    pass

# The definition of the tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time",
            "parameters": { "type": "object", "properties": {} },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of a location, the user should supply the location and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": { "type": "string", "description": "The city name" },
                    "date": { "type": "string", "description": "The date in format YYYY-mm-dd" },
                },
                "required": ["location", "date"]
            },
        }
    },
]

TOOLS = ["base_tools/get_weather"]

def add_task(
        task_name:str,
        model:str,
        task_content:str,
        available_tools = TOOLS,
):
    task = Task(task_name, model, task_content, available_tools)
    try:
        if submit_task(task):
            print("Success")
    except Exception as e:
        print(f"Submit Wrong:{e}")
    return


