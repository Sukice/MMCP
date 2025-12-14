# MMCP

---

```
src/          
├── __init__.py           
├── config/               # 全局配置
│   ├── __init__.py
│   └── settings.py       
├── user/                 # 【用户域】
│   ├── __init__.py
│   ├── task_client.py    # CLI接口（add_task）
│   └── web/              # WebUI 专属模块                
├── mcp_server/           # 【MCP服务器域】
│   ├── __init__.py
│   ├── task_manager.py   
│   ├── task_executor.py  
│   ├── model_manager.py  
│   └── 
├── plugin/               # 【MCP工具插件域】
│   ├── __init__.py
│   ├── tool_caller.py    
│   ├── base_plugin.py    
│   └── example_plugins/  
├── common/               # 【公共层】
│   ├── __init__.py
│   ├── models/           
│   └── utils/            
└── main.py               # 启动入口
```