import asyncio
import json
import threading
import re
from src.common.models import Task, ToolRecord
from src.common.utils import get_current_datetime, datetime_to_str, TaskLogger
from src.common.utils.model_utils import get_openai_client
from src.config.settings import MAX_COUNT, MAX_HANDLING_TASKS
from src.mcp_server.task_manager import (
    get_pending_task, add_handling_task, remove_handling_task,
    get_handling_task_count, requeue_task
)
from src.mcp_server.model_manager import get_model, update_model_state, bind_model_task, unbind_model_task
from src.common.utils.history_utils import write_task_history
from src.mcp_server.tool_manager import add_executing_tool, remove_executing_tool
from src.plugins.tool_call import call_plugin_function


async def execute_task_handler() -> None:
    """任务执行处理器（持续监控队列）"""
    print(">>> 任务执行处理器已启动，正在监听队列...")
    while True:
        try:
            if get_handling_task_count() >= MAX_HANDLING_TASKS:
                await asyncio.sleep(1.0)
                continue

            task = get_pending_task()
            if not task:
                await asyncio.sleep(1.0)
                continue

            # 捕获任务后不立即打印大段信息，交给 logger 在 execute_task 里打印
            model = get_model(task.model)
            if not model:
                print(f"警告：模型 {task.model} 未初始化，任务 {task.task_name} 重新入队")
                requeue_task(task)
                await asyncio.sleep(2.0)
                continue

            if model.state == "idle":
                update_model_state(task.model, "think")
                asyncio.create_task(execute_task(task))
            else:
                await asyncio.sleep(2)
                requeue_task(task)

        except Exception as e:
            print(f"Handler Loop 异常: {e}")
            await asyncio.sleep(1.0)


async def execute_task(task: Task) -> None:
    """执行单个任务"""
    add_handling_task(task)
    task.state = "handling"
    bind_model_task(task.model, task.task_id, task.task_name)

    # 使用从 utils 导入的 Logger
    logger = TaskLogger(task.task_id, task.task_name)
    logger.print_header(task)

    count = 0
    is_success = False

    try:
        while True:
            count += 1
            if count > MAX_COUNT:
                err_msg = f"任务执行超过最大次数（{MAX_COUNT}）"
                task.add_session_history({"role": "system", "content": err_msg})
                logger.log_error(err_msg)
                break

            update_model_state(task.model, "think")
            bind_model_task(task.model, task.task_id, task.task_name)

            # --- 模型调用 ---
            try:
                response = await model_call(task)

                if not response:
                    raise ValueError("模型未返回有效响应")

                # 累加 Token 消耗
                if hasattr(response, 'usage'):
                    logger.update_usage(response.usage)

                message = response.choices[0].message
                content = message.content
                reasoning = getattr(message, 'reasoning_content', None)
                tool_calls = message.tool_calls

                # 1. 打印思考
                logger.log_reasoning(reasoning)

                # 2. 打印回复内容
                logger.log_response(content)

                # 3. 打印工具调用
                tool_calls_dict = []
                if tool_calls:
                    for tool_call in tool_calls:
                        # 兼容处理
                        if hasattr(tool_call, 'model_dump'):
                            tool_dict = tool_call.model_dump()
                        else:
                            tool_dict = tool_call.dict()

                        if 'function' in tool_dict and 'arguments' in tool_dict['function']:
                            tool_dict['function']['arguments'] = tool_dict['function']['arguments'] or "{}"

                        tool_calls_dict.append(tool_dict)

                        # 日志显示调用
                        logger.log_tool_call(tool_call.function.name, tool_call.function.arguments)

                # 更新历史
                update_model_state(task.model, "wait")
                task.add_session_history({
                    'role': 'assistant',
                    'content': content,
                    'reasoning_content': reasoning,
                    'tool_calls': tool_calls_dict if tool_calls_dict else None,
                })

            except Exception as e:
                err_msg = f"模型调用异常: {str(e)}"
                logger.log_error(err_msg)
                task.add_session_history({"role": "system", "content": err_msg})
                break

            # --- 执行工具 ---
            if tool_calls:
                pending_tasks = []
                current_records = []

                for tool in tool_calls:
                    try:
                        name = tool.function.name
                        # 解析 mcp_type 和 func_name
                        match_mcp = re.match(r"^(.*?)__", name)
                        match_func = re.match(r"^.*?__(.*)$", name)

                        if not match_mcp or not match_func:
                            logger.log_error(f"工具名称格式错误: {name}")
                            continue

                        mcp_type = match_mcp.group(1)
                        func_name = match_func.group(1)
                        args = json.loads(tool.function.arguments)

                        record = ToolRecord(
                            task_id=task.task_id,
                            task_name=task.task_name,
                            call_id=tool.id,
                            mcp_type=mcp_type,
                            tool_name=func_name,
                            model=task.model,
                            call_time=datetime_to_str(get_current_datetime()),
                            state="executing",
                            arguments=args,
                        )

                        add_executing_tool(record)
                        current_records.append(record)
                        pending_tasks.append(asyncio.create_task(call_plugin_function(record)))

                    except Exception as e:
                        logger.log_error(f"准备工具失败: {e}")

                if pending_tasks:
                    results = await asyncio.gather(*pending_tasks, return_exceptions=True)

                    for i, result in enumerate(results):
                        record = current_records[i]
                        remove_executing_tool(record)

                        content_str = str(result)
                        if isinstance(result, Exception):
                            content_str = f"Error: {str(result)}"
                            logger.log_error(f"{record.tool_name} error: {content_str}")
                        else:
                            # 4. 打印工具返回结果
                            logger.log_tool_result(content_str)

                        task.add_session_history({
                            "role": "tool",
                            "tool_call_id": record.call_id,
                            "content": content_str
                        })
                continue
            else:
                # 任务正常结束
                is_success = True
                break

        task.state = "completed"
        task.finish_time = datetime_to_str(get_current_datetime())
        logger.print_footer(success=is_success)

    finally:
        remove_handling_task(task)
        update_model_state(task.model, "idle")
        unbind_model_task(task.model)
        write_task_history(task)


async def model_call(task: Task):
    if task.model == "deepseek-chat":
        client = get_openai_client(model_name=task.model)
        if not client:
            raise ValueError(f"无法获取模型客户端: {task.model}")

        # 使用 await 调用
        response = await client.chat.completions.create(
            model='deepseek-chat',
            messages=task.session_history,
            tools=task.get_tool_info(),
            extra_body={"thinking": {"type": "enabled"}}
        )
        return response
    return None


def start_execute_handler_thread():
    """在后台线程中启动 Event Loop"""

    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(execute_task_handler())
        loop.close()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    return t