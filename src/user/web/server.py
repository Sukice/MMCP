import os
import shutil
import zipfile
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# 导入项目模块
from src.mcp_server.model_manager import init_default_models, list_models, init_model, remove_model
from src.plugins.plugin_manager import (
    init_config_data, get_config_data, register_plugin, unregister_plugin,
    PLUGIN_COLLECTION_DIR
)
from src.mcp_server.task_executor import start_execute_handler_thread
from src.mcp_server.task_manager import _task_queue, _handling_task_list, init_task
from src.mcp_server.tool_manager import _executing_tool_list
from src.common.models import Task
from src.common.utils.task_logger import TASK_LOG_STORAGE
from src.config.settings import save_model_config, delete_model_config  # [新增导入]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">>> WebUI 启动中...")
    init_config_data()
    init_default_models()
    start_execute_handler_thread()
    yield
    print(">>> WebUI 关闭")


app = FastAPI(title="MMCP WebUI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateTaskRequest(BaseModel):
    name: str
    content: str
    tools: List[str] = None
    model: str = "deepseek-chat"


class PluginActionRequest(BaseModel):
    plugin_name: str
    delete_source: bool = False


class AddModelRequest(BaseModel):
    model_name: str
    base_url: str
    api_key: str


@app.get("/")
async def read_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "templates", "index.html")
    if not os.path.exists(template_path):
        return HTMLResponse(content="<h1>Error: template not found</h1>", status_code=404)
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/dashboard")
def get_dashboard_data():
    pending = [t.to_dict() for t in _task_queue]
    handling = [t.to_dict() for t in _handling_task_list]
    for t in pending: t['status_display'] = 'Waiting'
    for t in handling: t['status_display'] = 'Handling'

    models = [{"name": m.name, "state": m.state, "task_id": m.task_id, "task_name": m.task_name} for m in list_models()]
    tools = [t.to_dict() for t in _executing_tool_list]

    return {"tasks": handling + pending, "models": models, "tools": tools}


@app.get("/api/logs/{task_id}")
def get_task_logs(task_id: str):
    return TASK_LOG_STORAGE.get(task_id, [])


@app.post("/api/tasks")
def create_task(req: CreateTaskRequest):
    try:
        tools = req.tools if req.tools else ["base_tools"]
        new_task = Task(
            task_name=req.name,
            model=req.model,
            task_content=req.content,
            available_tools=tools
        )
        init_task(new_task)
        return {"status": "success", "task_id": new_task.task_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/models")
def api_add_model(req: AddModelRequest):
    if not req.model_name or not req.base_url or not req.api_key:
        raise HTTPException(status_code=400, detail="所有字段均为必填项")

    success = save_model_config(req.model_name, req.base_url, req.api_key)
    if not success:
        raise HTTPException(status_code=500, detail="保存配置失败")

    init_model(req.model_name)
    return {"status": "success"}


# [新增] 删除模型接口
@app.delete("/api/models/{model_name}")
def api_delete_model(model_name: str):
    # 1. 先从配置文件删除 (持久化层)
    success = delete_model_config(model_name)
    if not success:
        raise HTTPException(status_code=500, detail="删除配置失败")

    # 2. [新增] 再从内存池删除 (运行时层)
    remove_model(model_name)

    return {"status": "success"}


@app.get("/api/available_tools")
def get_available_tools_list():
    config = get_config_data()
    tool_list = []
    if config:
        for mcp_type, plugin_data in config.items():
            funcs = plugin_data.get("functions") or {}
            for func_name in funcs:
                tool_list.append(f"{mcp_type}/{func_name}")
    return tool_list


@app.get("/api/plugins")
def list_plugins():
    init_config_data()
    config = get_config_data() or {}
    plugins = []
    for k, v in config.items():
        if not isinstance(v, dict): v = {}
        funcs = v.get('functions') or {}
        plugins.append({
            "name": k,
            "desc": v.get('desc', '无描述'),
            "functions": funcs
        })
    return plugins


@app.post("/api/plugins/upload")
async def upload_plugin(file: UploadFile = File(...)):
    filename = file.filename
    if not filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="请上传 .zip 格式的插件包")
    plugin_name = filename[:-4]
    target_dir = os.path.join(PLUGIN_COLLECTION_DIR, plugin_name)
    temp_zip = os.path.join(PLUGIN_COLLECTION_DIR, f"temp_{filename}")
    try:
        with open(temp_zip, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        if os.path.exists(target_dir): shutil.rmtree(target_dir)
        os.makedirs(target_dir)
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        entries = os.listdir(target_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(target_dir, entries[0])) and entries[0] == plugin_name:
            inner_dir = os.path.join(target_dir, plugin_name)
            for item in os.listdir(inner_dir): shutil.move(os.path.join(inner_dir, item), target_dir)
            os.rmdir(inner_dir)
        if not os.path.exists(os.path.join(target_dir, "__init__.py")): raise HTTPException(status_code=400,
                                                                                            detail="缺少 __init__.py")
        if not os.path.exists(os.path.join(target_dir, f"{plugin_name}.yaml")): raise HTTPException(status_code=400,
                                                                                                    detail=f"缺少 {plugin_name}.yaml")
        success = register_plugin(plugin_name)
        if not success: raise HTTPException(status_code=500, detail="注册失败")
        return {"status": "success"}
    except Exception as e:
        if os.path.exists(target_dir): shutil.rmtree(target_dir)
        import traceback;
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_zip): os.remove(temp_zip)


@app.post("/api/plugins/unregister")
def api_unregister_plugin(req: PluginActionRequest):
    success = unregister_plugin(req.plugin_name)
    if not success: raise HTTPException(status_code=500, detail="注销配置失败")
    if req.delete_source:
        plugin_path = os.path.join(PLUGIN_COLLECTION_DIR, req.plugin_name)
        try:
            if os.path.exists(plugin_path): shutil.rmtree(plugin_path)
        except Exception as e:
            print(f"删除文件失败: {e}")
    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)