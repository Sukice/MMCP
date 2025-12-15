import time
import json
from collections import defaultdict
from src.common.models import Task

# --- 全局日志存储 ---
# 结构: { "task_id": [ {type: "reasoning", content: "..."}, ... ] }
TASK_LOG_STORAGE = defaultdict(list)


class TaskLogger:
    """负责任务执行过程中的流式日志输出"""
    # 颜色定义（保留用于控制台输出）
    c_reset = "\033[0m"
    c_dim = "\033[2m"
    c_red = "\033[31m"
    c_green = "\033[32m"
    c_yellow = "\033[33m"
    c_blue = "\033[34m"
    c_purple = "\033[35m"
    c_cyan = "\033[36m"
    c_white = "\033[37m"

    def __init__(self, task_id: str, task_name: str):
        self.start_time = time.time()
        self.task_id = task_id
        self.task_name = task_name
        self.usage = {"prompt": 0, "completion": 0, "total": 0}

    def _save_log(self, log_type: str, content: str):
        """保存结构化日志到内存"""
        TASK_LOG_STORAGE[self.task_id].append({
            "timestamp": time.time(),
            "type": log_type,
            "content": content
        })

    def print_header(self, task: Task):
        # 控制台输出
        print(f"\n{self.c_green}🔰 任务启动：{task.task_name}{self.c_reset}")
        print(f"   任务描述：{task.task_content}")
        print(f"   调用模型：{task.model}")
        print(f"{self.c_dim}┌── 🏃 执行记录 {'─' * 30}{self.c_reset}")

        # 内存存储
        self._save_log("header", f"任务启动：{task.task_name}\n描述：{task.task_content}\n模型：{task.model}")

    def log_line(self, content: str, color: str = ""):
        """打印带竖线的行（仅控制台）"""
        prefix = f"{self.c_dim}│{self.c_reset}"
        for line in content.split('\n'):
            print(f"{prefix} {color}{line}{self.c_reset}")

    def log_reasoning(self, content: str):
        if not content: return
        self.log_line(f"🧠 {content}", self.c_yellow)
        self._save_log("reasoning", content)

    def log_response(self, content: str):
        if not content: return
        self.log_line(f"🤖 {content}", self.c_purple)
        self._save_log("response", content)  # 只有这个会在前端渲染Markdown

    def log_tool_call(self, func_name: str, args_str: str):
        clean_name = func_name.split("__")[-1]
        try:
            args = json.loads(args_str)
            args_display = ",".join([f'{k}="{v}"' for k, v in args.items()])
        except:
            args_display = args_str

        call_str = f"{clean_name}({args_display})"
        self.log_line(f"🔨 {call_str}", self.c_cyan)
        self._save_log("tool_call", call_str)

    def log_tool_result(self, result: str):
        res_str = str(result)
        display_str = res_str if len(res_str) <= 100 else res_str[:100] + "..."
        self.log_line(f"📥 {display_str}", self.c_blue)
        # 存储时保留完整结果，或者也截断，看需求。这里存完整的方便查看
        self._save_log("tool_result", res_str)

    def log_error(self, error: str):
        self.log_line(f"❌ {error}", self.c_red)
        self._save_log("error", error)

    def update_usage(self, response_usage):
        if response_usage:
            self.usage["prompt"] += response_usage.prompt_tokens
            self.usage["completion"] += response_usage.completion_tokens
            self.usage["total"] += response_usage.total_tokens

    def print_footer(self, success: bool = True):
        duration = time.time() - self.start_time

        if success:
            end_line = f"{self.c_dim}└──{self.c_reset} {self.c_green}√ 任务完成{self.c_reset}"
            status_text = "√ 任务完成"
        else:
            end_line = f"{self.c_dim}└──{self.c_reset} {self.c_red}× 任务异常{self.c_reset}"
            status_text = "× 任务异常"

        print(end_line)
        stats = f"Token Usage: {self.usage['total']} (P:{self.usage['prompt']} + C:{self.usage['completion']})\nTotal Time : {duration:.2f}s"
        print(f"    {stats.replace(chr(10), chr(10) + '    ')}")  # 简单的缩进处理
        print("-" * 50 + "\n\n\n\n\n")

        self._save_log("footer", f"{status_text}\n{stats}")