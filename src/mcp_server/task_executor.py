import asyncio
from typing import List
from src.common.models import Task, ToolRecord
from src.common.utils import get_current_datetime, datetime_to_str
from src.common.utils.model_utils import get_openai_client
from src.config.settings import MAX_COUNT, MAX_HANDLING_TASKS
from src.mcp_server.task_manager import (
    get_pending_task, add_handling_task, remove_handling_task,
    get_handling_task_count
)
from src.mcp_server.model_manager import get_model, update_model_state, bind_model_task, unbind_model_task
from src.common.utils.history_utils import write_task_history
import re

from src.plugins.tool_call import call_plugin_function


async def execute_task_handler() -> None:
    """任务执行处理器（持续监控队列）"""
    while True:
        # 检查队列和处理中任务数
        if get_pending_task() and get_handling_task_count() < MAX_HANDLING_TASKS:
            task = get_pending_task()
            if not task:
                await asyncio.sleep(1.0)
                continue

            # 检查模型状态
            model = get_model(task.model)
            if not model:
                # 模型未初始化，放回队列?这里可以修改到全局变量吗？
                from src.mcp_server.task_manager import _task_queue
                _task_queue.append(task)
                await asyncio.sleep(1.0)
                continue

            if model.state == "idle":
                # 异步执行任务
                asyncio.create_task(execute_task(task))

        await asyncio.sleep(1.0)


async def execute_task(task: Task) -> None:
    """执行单个任务"""
    add_handling_task(task)
    task.state = "handling"
    model = get_model(task.model)
    count = 0

    try:
        while True:
            count += 1
            if count > MAX_COUNT:
                task.add_session_history({
                    "role": "system",
                    "content": f"任务执行超过最大次数（{MAX_COUNT}），强制结束"
                })
                break

            # 模型进入思考状态
            update_model_state(task.model, "think")
            bind_model_task(task.model, task.task_id, task.task_name)

            # 模型调用
            response = await model_call(task)
            update_model_state(task.model, "wait")

            task.add_session_history(response.choices[0].message)
            reasoning_content = response.choices[0].message.reasoning_content
            content = response.choices[0].message.content
            tool_calls = response.choices[0].message.tool_calls

            if tool_calls:
                pending_tasks: List[asyncio.Task] = []
                for tool in tool_calls:
                    name = tool.function.name
                    pattern = r"^(.*?)__"
                    mcp_type = re.match(pattern, name).group(1)
                    pattern = r"^.*?__(.*)$"
                    func_name = re.match(pattern, name).group(1)

                    # 创建工具调用记录
                    record = ToolRecord(
                        task_id=task.task_id,
                        task_name=task.task_name,
                        call_id=tool.id,
                        mcp_type=mcp_type,
                        tool_name=func_name,
                        model=task.model,
                        call_time=datetime_to_str(get_current_datetime()),
                        arguments=tool.arguments,

                    )
                    # 异步调用工具
                    pending_tasks.append(asyncio.create_task(call_plugin_function(record)))
                # 等待所有工具调用完成
                if pending_tasks:
                    results = await asyncio.gather(*pending_tasks)

                    for res in results:
                        task.add_session_history({
                            "role": "tool",
                            "tool_call_id": res.tool_call_id,
                            "content": res
                        })
                continue
            else:
                # 无工具调用，添加模型回复
                task.add_session_history({
                    "role": "assistant",
                    "content": content
                })
                break

        # 任务完成
        task.state = "completed"
        task.finish_time = datetime_to_str(get_current_datetime())
    finally:
        remove_handling_task(task)
        update_model_state(task.model, "idle")
        unbind_model_task(task.model)
        write_task_history(task)



async def model_call(task: Task):
    if task.model == "deepseek-chat":
        client = get_openai_client(model_name=task.model)
        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=task.session_history,
            tools=task.available_tools,
            extra_body={"thinking": {"type": "enabled"}}
        )

        return response
    return {}






def start_execute_handler() -> asyncio.Task:
    """启动任务处理器"""
    return asyncio.create_task(execute_task_handler())