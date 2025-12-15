<div align="center">
  <img src="./assets/Logo.png" width="2752" height="350" alt="MMCP Icon" />

  # 🔌 MMCP (Multiple-MCP)

  **让多模型多工具协作像“插插头”一样简单**

  [快速开始] • [插件开发] • [贡献代码]



  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
  ![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green?style=flat-square&logo=fastapi)
  ![Vue3](https://img.shields.io/badge/Frontend-Vue.js-orange?style=flat-square&logo=vue.js)
  ![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

</div>


---

## 📖 简介 (Introduction)

**MMCP** 是一个全栈式的 MCP (Model Context Protocol) 协作框架，它巧妙地融合了 **MCP服务器**、**用户端**、**AI模型** 与 **MCP工具**。

### 核心哲学：Python as a Plug 🔌
我们认为，工具的接入不应该被繁琐的协议所束缚。在 MMCP 的设计哲学中：
* **Python 包即插件**：如果你有一个 Python 包（Package），它天然就是一个 MCP 插件。你只需要一张“说明书”（`.yaml`），它就能立刻被大模型“看见”并调用。
* **万物皆可封装**：对于非 Python 编写的工具（如 C++、Go），只需提供一个轻量级的 Python 包装层（Wrapper），即可无缝融入 MMCP 生态。

### 🌟 亮点特性
* **⚡ 极速异步并发**：基于 `asyncio` 构建的高效核心，支持多模型、多任务同时“开工”，拒绝排队等待。
* **🎨 零门槛 WebUI**：我们为你精心打造了开箱即用的可视化界面。无需查阅文档，点击鼠标即可配置模型、管理插件、监控任务流。
* **🧠 实时思维可视化**：在 UI 上实时展示模型的思考路径（Reasoning）、工具调用参数及执行结果，让 AI 的“黑盒”变得透明。

<div align="center">
  <img src="./assets/WebUI.png" width="800" alt="WebUI Dashboard" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />
</div>


---

## 🚀 快速开始 (Quick Start)

### 1. 准备工作
```bash
# 克隆仓库
git clone https://github.com/Sukice/MMCP.git
cd MMCP

# 安装依赖
pip install fastapi uvicorn openai pyyaml requests httpx
````

### 2\. 启动方式（二选一）

#### 方式 A：WebUI 启动（🔥 强烈推荐，适合所有用户）

这是体验 MMCP 魅力的最佳方式。

```bash
# Windows / Linux / macOS
python -m src.user.web.server
```

启动成功后，请在浏览器访问：👉 `http://localhost:8000`

<div align="center">
  <img src="./assets/AddTask.png" width="800" alt="WebUI Dashboard" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />
</div>

> **在这里你可以：**
>
>   * 在“模型池”直接添加你的 DeepSeek / OpenAI API Key。
>   * 拖拽上传 `.zip` 格式的插件包。
>   * 像聊天一样发布任务，并围观 AI 干活。

#### 方式 B：代码启动（💻 适合开发者）

如果你喜欢掌控一切，可以通过代码手动配置。

1.  **配置模型**：在根目录创建 `models_config.json`：

    ```json
    {
      "models": ["deepseek-chat"],
      "api_keys": { "deepseek-chat": "sk-xxxxxx" },
      "base_urls": { "deepseek-chat": "https://api.deepseek.com" }
    }
    ```

2.  **编写运行脚本** (`test.py`)：

    ```python
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
            available_tools=["base_tools/get_current_time"], 
            task_content="现在几点了？"
        )
        
        # 任务2：查天气 (需要组合两个工具)
        add_task(
            model="deepseek-chat", 
            task_name="get_weather", 
            available_tools=["base_tools/get_weather", "base_tools/get_current_time"], 
            task_content="帮我查查今天广州的天气怎么样？"
        )

        print("4. 🚀 启动任务引擎 (按 Ctrl+C 停止)...")
        await execute_task_handler()

    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n🛑 服务已停止")
    ```

-----

## 🧩 插件开发指南 (Plugin Development)

想要扩展 AI 的能力？非常简单，只需两步！

### 步骤 1：编写代码 

在你的 Python 包中，定义你希望 AI 调用的函数。

```python
# src/plugins/plugin_collection/my_awesome_plugin/filename.py

def calculate_sum(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b
```

```python
# src/plugins/plugin_collection/my_awesome_plugin/__init__.py
from .filename import calculate_sum

__all__=['calculate_sum']
```


### 步骤 2：编写说明书 (`.yaml`)

告诉 AI 如何使用你的工具。文件名需与插件文件夹同名。

```yaml
# src/plugins/plugin_collection/my_awesome_plugin/my_awesome_plugin.yaml

my_awesome_plugin:  # 插件唯一标识 ID
  name: "超级计算器"
  desc: "提供基础的数学计算能力"
  dir_path: plugin_collection/my_awesome_plugin/
  
  functions:
    calculate_sum:
      type: function
      function:
        # 注意：命名规则必须是 插件名__函数名
        name: "my_awesome_plugin__calculate_sum"
        description: "计算两个整数的和"
        parameters:
          type: "object"
          properties:
            a:
              type: "integer"
              description: "第一个加数"
            b:
              type: "integer"
              description: "第二个加数"
          required: ["a", "b"]
```

### 📦 如何安装插件？

  * **WebUI 用户**：将插件文件夹打包为 `.zip`，在 Web 界面点击上传即可热加载。

<div align="center">
  <img src="./assets/RegisterPlugin.png" width="800" alt="WebUI Dashboard" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />
</div>

  * **命令行用户**：将文件夹放入 `src/plugins/plugin_collection/`，然后调用 `register_plugin("插件名")` 即可。

-----

## 🤝 社区与贡献 (Contribution)

MMCP 是一个开放的生态，我们非常欢迎你的加入！

  * **插件仓库**：寻找更多好玩的插件，或提交你的作品，请访问子仓库 [MMCP-plugin-source]<-正在筹划
  * **提交反馈**：遇到 Bug 或有新点子？欢迎提交 Issue。
  * **贡献代码**：Fork 本仓库 -\> 修改代码 -\> 提交 Pull Request。
  * **文档编写**：我需要一个协助写文档的助手！

让我们一起构建最简单、最好用的 MCP 框架！🌟

-----



