"""文件提交原语与单写者锁；所有失败均保留最后的有效项目清单。"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from PySide6.QtCore import QLockFile

from .errors import DesignerError, require
from .migrations import migrate
from .models import ProjectModel
from .validation import validate_project

logger = logging.getLogger(__name__)
MAX_PROJECT_BYTES = 32 * 1024 * 1024


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def file_token(path: Path) -> str | None:
    try:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()
    except FileNotFoundError:
        return None


def path_key(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))


class FileLease:
    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().resolve()
        self.lock = QLockFile(str(self.path) + ".lock")
        self.lock.setStaleLockTime(0)
        self.acquired = self.lock.tryLock(0)

    def release(self) -> None:
        if self.acquired:
            self.lock.unlock()
            self.acquired = False


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "项目文件包含重复字段。")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise DesignerError("项目文件不能包含非有限数字。")


@dataclass(frozen=True, slots=True)
class LoadedProject:
    model: ProjectModel
    token: str
    migrated: bool


def load_project(path: Path) -> LoadedProject:
    try:
        # 直接限制实际读取量，文件在读取期间变大也不能绕过容量边界。
        with path.open("rb") as stream:
            payload = stream.read(MAX_PROJECT_BYTES + 1)
        require(len(payload) <= MAX_PROJECT_BYTES, "项目文件超过当前支持的 32 兆字节，请先检查文件。")
        raw = json.loads(payload.decode("utf-8-sig"), object_pairs_hook=unique_object, parse_constant=reject_constant)
        model = ProjectModel.from_dict(migrate(raw))
        validate_project(model)
        return LoadedProject(model, digest(payload), raw["schema_version"] != 2)
    except DesignerError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        logger.exception("项目读取失败：%s", path)
        raise DesignerError("无法读取项目，请检查文件内容、编码和访问权限。") from exc


def resource_path(base: Path, value: str, checksum: str) -> Path:
    relative = PurePosixPath(value)
    require(len(checksum) == 64 and all(char in "0123456789abcdef" for char in checksum), "资源摘要格式无效。")
    require(not relative.is_absolute() and len(relative.parts) == 2 and relative.parts[0] == "assets"
            and relative.stem == checksum and "\\" not in value and ":" not in value
            and ".." not in relative.parts, "资源路径必须是项目内的内容摘要路径。")
    root = base.resolve()
    target = root.joinpath(*relative.parts).resolve()
    require(target.is_relative_to(root), "资源路径不能离开项目目录。")
    return target


def no_fault(stage: str) -> None:
    """生产默认检查点，不改变提交结果。"""


def atomic_write(path: Path, payload: bytes, checkpoint: Callable[[str], None] = no_fault,
                 label: str = "file") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".uiplay-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        checkpoint(label + ".staged")
        os.replace(temporary, path)
        checkpoint(label + ".replaced")
    except OSError:
        logger.exception("文件提交失败：%s", path)
        raise
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            logger.warning("暂存文件未能清理：%s", temporary)


def commit_project(path: Path, model: ProjectModel, *, expected_token: str | None,
                   resource_source: Path | None = None,
                   checkpoint: Callable[[str], None] = no_fault) -> str:
    """调用者持有目标写锁；资源完成后仅替换一个项目清单。"""
    validate_project(model)
    require(file_token(path) == expected_token, "磁盘项目已被外部修改，请重新打开或另存为。")
    payload = model.to_bytes()
    require(len(payload) <= MAX_PROJECT_BYTES,
            "项目内容超过当前支持的 32 兆字节，请减少或压缩图片等内容后保存；原项目和备份均未修改。")
    for resource in model.data["resources"]:
        target = resource_path(path.parent, resource["path"], resource["sha256"])
        if target.exists():
            require(file_token(target) == resource["sha256"], "已有资源内容被修改，已停止保存。")
            continue
        require(resource_source is not None, "缺少项目资源来源，无法完成保存。")
        source = resource_path(resource_source, resource["path"], resource["sha256"])
        require(source.is_file(), f"资源“{resource.get('name', '未命名资源')}”缺失，已停止保存。")
        content = source.read_bytes()
        require(digest(content) == resource["sha256"], "资源内容摘要不匹配，已停止保存。")
        atomic_write(target, content, checkpoint, "asset")
    checkpoint("resources.ready")
    require(file_token(path) == expected_token, "保存期间磁盘项目发生变化，已停止覆盖。")
    if expected_token is not None:
        previous = path.read_bytes()
        require(digest(previous) == expected_token, "旧项目已经变化，不能覆盖。")
        atomic_write(path.with_suffix(path.suffix + ".bak"), previous, checkpoint, "backup")
    require(file_token(path) == expected_token, "提交前磁盘项目发生变化，已停止覆盖。")
    atomic_write(path, payload, checkpoint, "manifest")
    return digest(payload)
