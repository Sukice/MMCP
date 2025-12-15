import os
import shutil
import zipfile
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# 导入项目模块
from src.mcp_server.model_manager import init_default_models, list_models
from src.plugins.plugin_manager import (
    init_config_data, get_config_data, register_plugin, unregister_plugin,
    PLUGIN_COLLECTION_DIR, GLOBAL_TOOL_YAML
)
from src.mcp_server.task_executor import start_execute_handler_thread
from src.mcp_server.task_manager import _task_queue, _handling_task_list, init_task
from src.mcp_server.tool_manager import _executing_tool_list
from src.common.models import Task
import yaml

app = FastAPI(title="MMCP WebUI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 数据模型 ---
class CreateTaskRequest(BaseModel):
    name: str
    content: str
    tools: List[str]
    model: str = "deepseek-chat"


class PluginActionRequest(BaseModel):
    plugin_name: str


# --- 生命周期 ---
@app.on_event("startup")
async def startup_event():
    print(">>> WebUI 启动中...")
    init_config_data()
    init_default_models()
    start_execute_handler_thread()


# --- API 接口 ---

@app.get("/")
async def read_root():
    """返回前端页面"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/dashboard")
def get_dashboard_data():
    """聚合接口：一次性获取任务、模型、工具状态，减少请求闪烁"""
    # 任务
    pending = [t.to_dict() for t in _task_queue]
    handling = [t.to_dict() for t in _handling_task_list]
    for t in pending: t['status_display'] = 'Waiting'
    for t in handling: t['status_display'] = 'Handling'

    # 模型
    models = [
        {"name": m.name, "state": m.state, "task_id": m.task_id, "task_name": m.task_name}
        for m in list_models()
    ]

    # 工具
    tools = [t.to_dict() for t in _executing_tool_list]

    return {
        "tasks": handling + pending,
        "models": models,
        "tools": tools
    }


@app.post("/api/tasks")
def create_task(req: CreateTaskRequest):
    try:
        if not req.tools:
            req.tools = ["base_tools/get_current_time"]
        new_task = Task(
            task_name=req.name,
            model=req.model,
            task_content=req.content,
            available_tools=req.tools
        )
        init_task(new_task)
        return {"status": "success", "task_id": new_task.task_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/available_tools")
def get_available_tools_list():
    config = get_config_data()
    tool_list = []
    if config:
        for mcp_type, plugin_data in config.items():
            if "functions" in plugin_data:
                for func_name in plugin_data["functions"]:
                    tool_list.append(f"{mcp_type}/{func_name}")
    return tool_list


# --- 插件管理 API ---

@app.get("/api/plugins")
def list_plugins():
    """列出 tool.yaml 中已注册的插件"""
    config = get_config_data() or {}
    return [{"name": k, "desc": v.get('desc', '无描述')} for k, v in config.items()]


@app.post("/api/plugins/upload")
async def upload_plugin(file: UploadFile = File(...)):
    """上传并注册插件 (zip格式)"""
    filename = file.filename
    if not filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="请上传 .zip 格式的插件包")

    plugin_name = filename[:-4]  # 去掉 .zip
    target_dir = os.path.join(PLUGIN_COLLECTION_DIR, plugin_name)

    # 1. 保存临时文件
    temp_zip = os.path.join(PLUGIN_COLLECTION_DIR, f"temp_{filename}")
    try:
        with open(temp_zip, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. 清理旧目录（如果存在）
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir)

        # 3. 解压
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

        # 4. 目录层级调整（如果解压出来包了一层文件夹，则移动出来）
        # 检查是否解压后里面只有个 plugin_name 文件夹
        entries = os.listdir(target_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(target_dir, entries[0])) and entries[0] == plugin_name:
            inner_dir = os.path.join(target_dir, plugin_name)
            for item in os.listdir(inner_dir):
                shutil.move(os.path.join(inner_dir, item), target_dir)
            os.rmdir(inner_dir)

        # 5. 校验关键文件
        if not os.path.exists(os.path.join(target_dir, "__init__.py")):
            raise HTTPException(status_code=400, detail="插件包缺少 __init__.py")
        if not os.path.exists(os.path.join(target_dir, f"{plugin_name}.yaml")):
            raise HTTPException(status_code=400, detail=f"插件包缺少 {plugin_name}.yaml")

        # 6. 注册
        success = register_plugin(plugin_name)
        if not success:
            raise HTTPException(status_code=500, detail="插件注册失败，请检查服务器日志")

        return {"status": "success", "message": f"插件 {plugin_name} 已成功安装并注册"}

    except Exception as e:
        # 出错清理目录
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)


@app.post("/api/plugins/unregister")
def api_unregister_plugin(req: PluginActionRequest):
    success = unregister_plugin(req.plugin_name)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="注销失败")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)