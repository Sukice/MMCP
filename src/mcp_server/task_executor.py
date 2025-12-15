import asyncio
import json
import threading
import re
from src.common.models import Task, ToolRecord
from src.common.utils import get_current_datetime, datetime_to_str
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
    print("任务执行处理器已启动，正在监听队列...")
    while True:
        try:
            # 1. 检查是否达到最大并发数
            if get_handling_task_count() >= MAX_HANDLING_TASKS:
                await asyncio.sleep(1.0)
                continue

            # 2. 获取任务
            task = get_pending_task()

            if not task:
                await asyncio.sleep(1.0)
                continue
            print(f"捕获任务：{task.task_name}")
            # 3. 检查模型状态
            model = get_model(task.model)
            if not model:
                print(f"警告：模型 {task.model} 未初始化，任务 {task.task_name} 重新入队")
                requeue_task(task)
                await asyncio.sleep(2.0)  # 稍微等待，避免CPU空转
                continue

            if model.state == "idle":
                # 4. 异步执行任务
                update_model_state(task.model, "think")
                asyncio.create_task(execute_task(task))
            else:
                print(f"{task.model} 模型忙碌，任务 {task.task_name} 重新入队")
                await asyncio.sleep(10)
                requeue_task(task)

        except Exception as e:
            print(f"Handler Loop 异常: {e}")
            await asyncio.sleep(1.0)


async def execute_task(task: Task) -> None:
    """执行单个任务"""
    add_handling_task(task)
    task.state = "handling"
    print(f">>> 开始执行任务：{task.task_name}")
    bind_model_task(task.model, task.task_id, task.task_name)
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

            # 绑定模型状态
            update_model_state(task.model, "think")
            bind_model_task(task.model, task.task_id, task.task_name)

            # --- 模型调用 (关键修改：await) ---
            try:
                response = await model_call(task)

                if not response:
                    raise ValueError("模型未返回有效响应")
                print(response)
                message = response.choices[0].message
                content = message.content
                tool_calls = message.tool_calls

                tool_calls_dict = []
                if tool_calls:
                    for tool_call in tool_calls:
                        # 兼容 Pydantic v2（model_dump）和 v1（dict）
                        if hasattr(tool_call, 'model_dump'):
                            tool_dict = tool_call.model_dump()
                        else:
                            tool_dict = tool_call.dict()
                        if 'function' in tool_dict and 'arguments' in tool_dict['function']:
                            tool_dict['function']['arguments'] = tool_dict['function']['arguments'] or "{}"

                        tool_calls_dict.append(tool_dict)

                # 更新状态
                update_model_state(task.model, "wait")

                # 记录 Assistant 历史
                task.add_session_history({
                    'role': 'assistant',
                    'content': content,
                    'reasoning_content': getattr(message, 'reasoning_content', None),
                    'tool_calls': tool_calls_dict if tool_calls_dict else None,  # 注意：有些序列化可能需要处理对象转dict
                })

            except Exception as e:
                print(f"调用模型时出错：{e}")
                # 出错时释放模型并退出
                task.add_session_history({"role": "system", "content": f"模型调用异常: {str(e)}"})
                break

            # --- 处理工具调用 ---
            if tool_calls:
                pending_tasks = []
                # 临时保存记录以便回调后清理
                current_records = []

                for tool in tool_calls:
                    try:
                        name = tool.function.name
                        # 健壮的正则匹配
                        match_mcp = re.match(r"^(.*?)__", name)
                        match_func = re.match(r"^.*?__(.*)$", name)

                        if not match_mcp or not match_func:
                            print(f"错误：工具名称格式不正确: {name}")
                            continue

                        mcp_type = match_mcp.group(1)
                        func_name = match_func.group(1)

                        args = json.loads(tool.function.arguments)
                        print(f"调用工具: {func_name} 参数: {args}")

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

                        # 创建异步任务
                        pending_tasks.append(asyncio.create_task(call_plugin_function(record)))

                    except Exception as e:
                        print(f"解析工具参数失败: {e}")

                if pending_tasks:
                    # 等待所有工具并发执行完成
                    results = await asyncio.gather(*pending_tasks, return_exceptions=True)

                    for i, result in enumerate(results):
                        record = current_records[i]
                        remove_executing_tool(record)

                        content_str = str(result)
                        if isinstance(result, Exception):
                            content_str = f"Error: {str(result)}"

                        task.add_session_history({
                            "role": "tool",
                            "tool_call_id": record.call_id,
                            "content": content_str
                        })
                continue  # 继续下一轮循环，将工具结果发给模型
            else:
                # 无工具调用，任务结束
                break

        # 任务完成
        task.state = "completed"
        task.finish_time = datetime_to_str(get_current_datetime())
        print(f"<<< 任务完成：{task.task_name}")

    finally:
        remove_handling_task(task)
        update_model_state(task.model, "idle")
        unbind_model_task(task.model)
        write_task_history(task)


async def model_call(task: Task):
    if task.model == "deepseek-chat":
        # 获取异步客户端
        client = get_openai_client(model_name=task.model)
        if not client:
            raise ValueError(f"无法获取模型客户端: {task.model}")

        # 使用 await
        response = await client.chat.completions.create(
            model='deepseek-chat',
            messages=task.session_history,
            tools=task.get_tool_info(),
            extra_body={"thinking": {"type": "enabled"}}
        )
        print("模型返回成功")
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