import src
from src.mcp_server.model_manager import init_default_models
from src.mcp_server.task_executor import execute_task_handler, start_execute_handler
from src.user.task_client import add_task


# The mocked version of the tool calls



if __name__=="__main__":
    # 初始化默认模型
    init_default_models()
    # MCP服务器开启监控
    start_execute_handler()

    # 用户添加了任务
    add_task(model="deepseek-chat",task_name="get_time",task_content="Tell me what time is it now.")



