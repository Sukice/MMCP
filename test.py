import asyncio
from src.mcp_server.model_manager import init_default_models
from src.plugins.plugin_manager import init_config_data
from src.user.task_client import add_task
from src.mcp_server.task_executor import execute_task_handler


async def main():
    print("1. ♻️  加载插件配置...")
    init_config_data()

    print("2. 🤖 初始化模型池...")
    init_default_models()

    print("3. 📝 发布任务...")
    # 任务1：查时间
    add_task(
        model="deepseek-chat",
        task_name="get_time",
        available_tools=["mock/get_current_time"],
        task_content="现在几点了？"
    )

    # 任务2：查天气 (需要组合两个工具)
    add_task(
        model="deepseek-chat",
        task_name="get_weather",
        available_tools=["mock"],
        task_content="帮我查查今天广州的天气怎么样？"
    )

    print("4. 🚀 启动任务引擎 (按 Ctrl+C 停止)...")
    await execute_task_handler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")






