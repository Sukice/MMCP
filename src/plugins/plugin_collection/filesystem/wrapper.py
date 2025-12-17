from .mcp_bridge import get_bridge

# 1. 基础读写
async def read_text_file(path: str):
    """读取文本文件"""
    return await get_bridge().call_tool("read_text_file", {"path": path})

async def write_file(path: str, content: str):
    """写入文件 (覆盖)"""
    return await get_bridge().call_tool("write_file", {"path": path, "content": content})

# 2. 高级读取
async def read_media_file(path: str):
    """读取媒体文件 (返回Base64)"""
    return await get_bridge().call_tool("read_media_file", {"path": path})

async def read_multiple_files(paths: list):
    """同时读取多个文件"""
    return await get_bridge().call_tool("read_multiple_files", {"paths": paths})

# 3. 高级编辑
async def edit_file(path: str, edits: list, dryRun: bool = False):
    """
    智能编辑文件
    edits 结构示例: [{"oldText": "foo", "newText": "bar"}]
    """
    return await get_bridge().call_tool("edit_file", {
        "path": path,
        "edits": edits,
        "dryRun": dryRun
    })

# 4. 目录操作
async def create_directory(path: str):
    """创建目录"""
    return await get_bridge().call_tool("create_directory", {"path": path})

async def list_directory(path: str):
    """列出目录"""
    return await get_bridge().call_tool("list_directory", {"path": path})

async def list_directory_with_sizes(path: str):
    """列出目录 (带文件大小)"""
    return await get_bridge().call_tool("list_directory_with_sizes", {"path": path})

async def move_file(source: str, destination: str):
    """移动或重命名文件/目录"""
    return await get_bridge().call_tool("move_file", {"source": source, "destination": destination})

async def directory_tree(path: str):
    """获取递归目录树结构"""
    return await get_bridge().call_tool("directory_tree", {"path": path})

# 5. 搜索与信息
async def search_files(path: str, pattern: str, excludePatterns: list = []):
    """搜索文件"""
    return await get_bridge().call_tool("search_files", {
        "path": path,
        "pattern": pattern,
        "excludePatterns": excludePatterns
    })

async def get_file_info(path: str):
    """获取文件元数据 (时间、权限等)"""
    return await get_bridge().call_tool("get_file_info", {"path": path})

async def list_allowed_directories():
    """列出允许访问的根目录"""
    return await get_bridge().call_tool("list_allowed_directories", {})