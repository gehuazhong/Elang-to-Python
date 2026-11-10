"""验证不可变资源与单一清单提交，前提是调用者已持有写锁。"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping
from uuid import uuid4

from .contracts import ContractError, Project, canonical_bytes, require, validate_project

logger = logging.getLogger(__name__)
Checkpoint = Callable[[str], None]


def no_fault(stage: str) -> None:
    """正常运行的检查点不引入额外副作用。"""


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def file_token(path: Path) -> str | None:
    try:
        return digest(path.read_bytes())
    except FileNotFoundError:
        return None


def _relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    require(bool(value) and not path.is_absolute() and ".." not in path.parts
            and "\\" not in value and ":" not in value, "文件路径必须是项目内的相对路径。")
    return path


def atomic_write(path: Path, payload: bytes, checkpoint: Checkpoint, label: str) -> None:
    """同目录暂存后替换；没有直接覆盖原文件的回退路径。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".uiplay-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        checkpoint(f"{label}.staged")
        os.replace(temporary, path)
        checkpoint(f"{label}.replaced")
    except OSError:
        logger.exception("文件提交失败，目标为：%s", path)
        raise
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            logger.warning("暂存文件未能清理，将交由后续恢复检查处理：%s", temporary)


@dataclass(frozen=True)
class CommitReceipt:
    """提交结果使用预先计算的摘要，避免提交后再读文件导致回执不确定。"""

    token: str
    path: Path


def commit_project(
    path: Path,
    project: Project,
    resource_bytes: Mapping[str, bytes],
    *,
    expected_token: str | None,
    checkpoint: Checkpoint = no_fault,
) -> CommitReceipt:
    """先完成内容寻址资源，再备份并提交项目清单。"""
    validate_project(project)
    require(file_token(path) == expected_token, "磁盘文件已被其他写入者修改。")
    payload = canonical_bytes(project)
    for resource in project["resources"]:
        relative = _relative_path(resource["path"])
        expected_hash = resource["sha256"]
        require(len(relative.parts) == 2 and relative.parts[0] == "assets"
                and relative.stem == expected_hash, "资源文件名必须由内容摘要确定。")
        target = path.parent.joinpath(*relative.parts)
        supplied = resource_bytes.get(resource["id"])
        if supplied is not None:
            require(digest(supplied) == expected_hash, "导入资源的内容摘要不匹配。")
        if target.exists():
            require(file_token(target) == expected_hash, "已有资源的内容被修改。")
        else:
            require(supplied is not None, "缺少尚未落盘的资源内容。")
            atomic_write(target, supplied, checkpoint, "asset")
    checkpoint("resources.ready")
    require(file_token(path) == expected_token, "保存过程中磁盘文件发生变化。")
    if expected_token is not None:
        previous = path.read_bytes()
        require(digest(previous) == expected_token, "旧版本已变化，不能覆盖。")
        atomic_write(path.with_suffix(path.suffix + ".bak"), previous, checkpoint, "backup")
    require(file_token(path) == expected_token, "提交前检测到外部修改。")
    atomic_write(path, payload, checkpoint, "manifest")
    return CommitReceipt(digest(payload), path)


def verify_project_files(path: Path) -> Project:
    """验证提交后每个资源引用仍对应正确字节。"""
    project: Project = json.loads(path.read_text(encoding="utf-8"))
    validate_project(project)
    for resource in project["resources"]:
        relative = _relative_path(resource["path"])
        require(file_token(path.parent.joinpath(*relative.parts)) == resource["sha256"],
                "项目引用的资源缺失或内容不一致。")
    return project


def publish_generation(
    root: Path,
    files: Mapping[str, bytes],
    *,
    expected_token: str | None,
    checkpoint: Checkpoint = no_fault,
) -> CommitReceipt:
    """导出只发布一个版本指针，现有生成目录和业务文件保持各自所有权。"""
    require("ui_main.py" in files, "生成版本缺少界面文件。")
    current = root / "current.json"
    require(file_token(current) == expected_token, "导出版本已经被其他写入者修改。")
    generation_id = str(uuid4())
    generation = root / "generated" / generation_id
    records: list[dict[str, str]] = []
    for name, payload in sorted(files.items()):
        relative = _relative_path(name)
        require(relative.parts and relative.parts[0] not in {"handlers.py", "main.py"},
                "生成内容不能覆盖业务文件或稳定入口。")
        atomic_write(generation.joinpath(*relative.parts), payload, checkpoint, f"export.{name}")
        records.append({"path": name, "sha256": digest(payload)})
    checkpoint("export.files_ready")
    manifest = {
        "format": "uiplay.export", "schema_version": 1,
        "generation_id": generation_id, "files": records,
    }
    require(file_token(current) == expected_token, "导出发布前检测到版本变化。")
    atomic_write(current, canonical_bytes(manifest), checkpoint, "export.pointer")
    return CommitReceipt(digest(canonical_bytes(manifest)), current)


def read_generation(root: Path) -> dict[str, bytes]:
    """入口只读一次版本指针，所有文件都从同一个版本目录取得。"""
    manifest = json.loads((root / "current.json").read_text(encoding="utf-8"))
    generation_name = manifest["generation_id"]
    require(len(_relative_path(generation_name).parts) == 1, "生成版本目录无效。")
    generation = root / "generated" / generation_name
    result: dict[str, bytes] = {}
    for record in manifest["files"]:
        relative = _relative_path(record["path"])
        payload = generation.joinpath(*relative.parts).read_bytes()
        require(digest(payload) == record["sha256"], "生成版本包含不一致的文件。")
        result[record["path"]] = payload
    return result
