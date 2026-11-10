"""读取父进程提供的管道，兼容没有控制台的 Windows 便携包。"""

from __future__ import annotations

import os
import sys
from typing import BinaryIO


def inherited_pipe(kind: str) -> BinaryIO:
    stream = sys.stdin if kind == "input" else sys.stdout
    if stream is not None:
        binary = stream.buffer
        return getattr(binary, "raw", binary) if kind == "input" else binary
    if os.name != "nt":
        raise RuntimeError("预览进程缺少标准输入输出管道。")
    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    kernel.GetFileType.argtypes = [wintypes.HANDLE]
    kernel.GetFileType.restype = wintypes.DWORD
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.DuplicateHandle.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE,
                                      ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.DuplicateHandle.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    source = kernel.GetStdHandle(wintypes.DWORD(-10 if kind == "input" else -11))
    if not source or kernel.GetFileType(source) != 3:
        raise RuntimeError("预览只能由设计器通过受控管道启动。")
    process = kernel.GetCurrentProcess()
    duplicate = wintypes.HANDLE()
    if not kernel.DuplicateHandle(process, source, process, ctypes.byref(duplicate), 0, False, 2):
        raise OSError(ctypes.get_last_error(), "无法复制预览管道句柄。")
    try:
        descriptor = msvcrt.open_osfhandle(duplicate.value, os.O_BINARY | (os.O_RDONLY if kind == "input" else os.O_WRONLY))
    except OSError:
        kernel.CloseHandle(duplicate)
        raise
    # 描述符接管复制句柄；不修改父进程或原始标准句柄的所有权。
    return os.fdopen(descriptor, "rb" if kind == "input" else "wb", buffering=0)
