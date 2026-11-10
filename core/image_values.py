"""图片以受限的静态图像快照保存，校验不依赖 Qt。"""

from __future__ import annotations

import base64
import binascii
from functools import lru_cache
import hashlib
import struct
from typing import Any

from .errors import DesignerError, require

MAX_IMAGE_BYTES = 2 * 1024 * 1024


def normalize_image(value: Any) -> str:
    require(isinstance(value, str), "图片数据必须为文本编码。")
    require(len(value) <= (MAX_IMAGE_BYTES + 2) // 3 * 4, "单张图片不能超过两兆字节，请缩小后导入。")
    if value:
        image_bytes(value)
    return value


@lru_cache(maxsize=8)
def image_bytes(value: str) -> bytes:
    try:
        payload = base64.b64decode(value, validate=True)
        require(len(payload) <= MAX_IMAGE_BYTES and len(payload) >= 33 and payload[:8] == b'\x89PNG\r\n\x1a\n'
                and payload[12:16] == b'IHDR', "图片快照不是有效的静态图像。")
        width, height = struct.unpack('>II', payload[16:24])
        require(0 < width <= 4096 and 0 < height <= 4096 and width * height <= 8_000_000,
                "图片尺寸不能超过四千零九十六像素，且总像素不能超过八百万。")
        return payload
    except (ValueError, binascii.Error, struct.error) as exc:
        raise DesignerError("图片编码损坏，无法加载。") from exc


def image_filename(value: str) -> str:
    return "assets/" + hashlib.sha256(image_bytes(value)).hexdigest() + ".png"
