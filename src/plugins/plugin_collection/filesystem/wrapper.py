import os
# 引入 ALLOWED_PATH 和 get_bridge
from .mcp_bridge import get_bridge, ALLOWED_PATH


# ==========================================================
# 🛡️ 核心辅助函数：绝对路径转换 + 安全性核查
# ==========================================================
def _get_safe_path(path: str) -> str:
    """
    1. 将输入路径转换为绝对路径 (os.path.abspath)
    2. 执行安全性核查: 确保目标路径包含在 ALLOWED_PATH 内
    """
    # 强制转换为绝对路径，解决所有 ../ 和 ./ 的问题
    abs_path = os.path.abspath(path)

    # 严格按照要求：检测 "被允许的目录" 是否 in "调用的文件路径"
    if ALLOWED_PATH not in abs_path:
        raise PermissionError(f"⚠️ 安全拦截: 路径 '{abs_path}' 超出了允许的范围 '{ALLOWED_PATH}'！")

    return abs_path


# ==========================================================
# 1. 基础读写
# ==========================================================
async def read_text_file(path: str):
    """读取文本文件"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("read_text_file", {"path": safe_path})


async def write_file(path: str, content: str):
    """写入文件 (覆盖)"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("write_file", {"path": safe_path, "content": content})


# ==========================================================
# 2. 高级读取
# ==========================================================
async def read_media_file(path: str):
    """读取媒体文件 (返回Base64)"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("read_media_file", {"path": safe_path})


async def read_multiple_files(paths: list):
    """同时读取多个文件"""
    # 使用列表推导式批量检查并转换
    safe_paths = [_get_safe_path(p) for p in paths]
    return await get_bridge().call_tool("read_multiple_files", {"paths": safe_paths})


# ==========================================================
# 3. 高级编辑
# ==========================================================
async def edit_file(path: str, edits: list, dryRun: bool = False):
    """智能编辑文件"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("edit_file", {
        "path": safe_path,
        "edits": edits,
        "dryRun": dryRun
    })


# ==========================================================
# 4. 目录操作
# ==========================================================
async def create_directory(path: str):
    """创建目录"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("create_directory", {"path": safe_path})


async def list_directory(path: str):
    """列出目录"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("list_directory", {"path": safe_path})


async def list_directory_with_sizes(path: str):
    """列出目录 (带文件大小)"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("list_directory_with_sizes", {"path": safe_path})


async def move_file(source: str, destination: str):
    """移动或重命名文件/目录"""
    # ⚠️ 注意：源路径和目标路径都需要进行安全检查
    safe_source = _get_safe_path(source)
    safe_dest = _get_safe_path(destination)
    return await get_bridge().call_tool("move_file", {"source": safe_source, "destination": safe_dest})


async def directory_tree(path: str):
    """获取递归目录树结构"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("directory_tree", {"path": safe_path})


# ==========================================================
# 5. 搜索与信息
# ==========================================================
async def search_files(path: str, pattern: str, excludePatterns: list = []):
    """搜索文件"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("search_files", {
        "path": safe_path,
        "pattern": pattern,
        "excludePatterns": excludePatterns
    })


async def get_file_info(path: str):
    """获取文件元数据 (时间、权限等)"""
    safe_path = _get_safe_path(path)
    return await get_bridge().call_tool("get_file_info", {"path": safe_path})


async def list_allowed_directories():
    """列出允许访问的根目录"""
    # 不需要参数，直接透传
    return await get_bridge().call_tool("list_allowed_directories", {})