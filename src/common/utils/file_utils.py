import base64
import mimetypes
import os
import logging
from typing import List, Dict, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

logger = logging.getLogger(__name__)

TYPE_MAPPING = {
    'image': {'api_type': 'image_url', 'key_name': 'image_url'},
    'video': {'api_type': 'video_url', 'key_name': 'video_url'},
    'audio': {'api_type': 'audio_url', 'key_name': 'audio_url'}
}


def get_file_type(file_path: str):
    ext = os.path.splitext(file_path)[1].lower().strip('.')
    valid_types = {
        'pdf': {'pdf'},
        'image': {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff'},
        'video': {'mp4', 'mkv', 'mov', 'avi', 'webm'},
        'audio': {'mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg'}
    }
    for category, extensions in valid_types.items():
        if ext in extensions:
            return category
    return None


def _pdf_to_images_payload(file_path: str, max_pages: int = 1) -> List[Dict[str, Any]]:
    """
    核心逻辑：将 PDF 每一页切成图片，转 Base64
    """
    if not fitz:
        return [{"type": "text", "text": "[System Error: PyMuPDF not installed]"}]

    payloads = []
    try:
        doc = fitz.open(file_path)
        # 限制页数，防止 Token 爆炸或 Payload 过大
        total_pages = len(doc)
        process_pages = min(total_pages, max_pages)

        if total_pages > max_pages:
            logger.warning(f"PDF too long ({total_pages} pages). Only processing first {max_pages} pages.")

        for page_num in range(process_pages):
            page = doc.load_page(page_num)

            # 设置缩放比例，2.0 表示 2 倍清晰度 (适合 OCR)
            # 如果报错 Payload too large，可以改回 1.0 或 1.5
            mat = fitz.Matrix(2, 2)

            pix = page.get_pixmap(matrix=mat)

            # 转为 PNG 二进制
            img_data = pix.tobytes("png")
            pix.save(f"debug_page_{page_num}.png")
            b64_str = base64.b64encode(img_data).decode('utf-8')

            # 构造 Vision Payload
            payloads.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_str}",
                    "detail": "high"  # 提示模型这是高清图
                }
            })

        doc.close()

        # 如果截断了，可以在最后加一个提示文本（可选，视模型兼容性而定）
        if total_pages > max_pages:
            payloads.append({
                "type": "text",
                "text": f"\n[System Note: Only the first {max_pages} of {total_pages} pages were processed due to size limits.]"
            })

        return payloads

    except Exception as e:
        logger.error(f"PDF conversion failed: {e}")
        return [{"type": "text", "text": f"[Error processing PDF images: {str(e)}]"}]


def build_file_metadata(file_path: str) -> List[Dict[str, Any]]:
    """
    统一返回 List[Dict]。
    即使是单张图片，也返回包含一个元素的列表。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件未找到: {file_path}")

    file_type = get_file_type(file_path)

    # === 分支 1: PDF (切图) ===
    if file_type == 'pdf':
        return _pdf_to_images_payload(file_path)

    # === 分支 2: 其他多模态文件 (Image/Video/Audio) ===
    # 下面的逻辑保持处理单文件，但返回 List 格式

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        if file_type == 'image':
            mime_type = 'image/jpeg'

        else:
            # 兜底：当作纯文本处理
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return [{"type": "text", "text": f"\n\n=== File: {os.path.basename(file_path)} ===\n{f.read()}"}]
            except:
                raise ValueError(f"Unknown file type: {file_path}")

    try:
        with open(file_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Read file failed: {e}")

    config = TYPE_MAPPING.get(file_type, TYPE_MAPPING['image'])

    payload = {
        "type": config['api_type'],
        config['key_name']: {
            "url": f"data:{mime_type};base64,{b64_str}"
        }
    }

    return [payload]  # 注意这里返回 List