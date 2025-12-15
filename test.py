import asyncio
from src.mcp_server.model_manager import init_default_models
from src.plugins.plugin_manager import init_config_data
from src.user.task_client import add_task
from src.mcp_server.task_executor import execute_task_handler


async def main():
    print("1. 初始化配置...")
    init_config_data()

    print("2. 初始化默认模型...")
    init_default_models()

    print("3. 添加任务...")
    # 注意：这里需要确保 model 名和 init_default_models 里的一致
    add_task(model="deepseek-chat", task_name="get_time", available_tools=["base_tools/get_current_time"], task_content="Tell me what time is it now.")
    add_task(model="deepseek-chat", task_name="get_weather", available_tools=["base_tools/get_weather","base_tools/get_current_time"], task_content="Tell me what is the weather today in GuangZhou.")
    add_task(model="deepseek-chat", task_name="get_time", available_tools=["base_tools/get_current_time"], task_content="Tell me what time is it now.")

    print("4. 启动处理循环...")
    # 这会阻塞主线程，直到手动停止
    await execute_task_handler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("停止服务")






