"""通过写入失败与真实进程退出验证单清单提交协议。"""

from __future__ import annotations

import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from architecture_checks import storage_probe
from architecture_checks.contracts import ContractError, Project
from architecture_checks.storage_probe import (
    commit_project, digest, file_token, publish_generation,
    read_generation, verify_project_files,
)


def with_resource(project: Project, payload: bytes) -> tuple[Project, dict[str, bytes]]:
    result = deepcopy(project)
    checksum = digest(payload)
    identifier = "40f4a4ad-b02b-4fc6-9f37-0d803a5d2fdd"
    result["resources"] = [{
        "id": identifier, "name": "验证资源", "kind": "binary",
        "path": f"assets/{checksum}.bin", "sha256": checksum,
    }]
    return result, {identifier: payload}


def crash(kind: str, path: Path, stage: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, "-m", "architecture_checks.crash_worker", kind, str(path), stage],
        cwd=Path(__file__).resolve().parents[2], env=environment,
        capture_output=True, text=True, encoding="utf-8", timeout=20, check=False,
    )


@pytest.mark.parametrize("stage", [
    "asset.staged", "asset.replaced", "resources.ready", "backup.staged",
    "backup.replaced", "manifest.staged", "manifest.replaced",
])
def test_process_exit_leaves_complete_old_or_new_project(
    project: Project, tmp_path: Path, stage: str,
) -> None:
    old, resources = with_resource(project, b"original-resource")
    old["name"] = "旧版本"
    path = tmp_path / "中文项目.uipro"
    commit_project(path, old, resources, expected_token=None)
    result = crash("project", path, stage)
    assert result.returncode == 86, f"检查点未触发：{result.stdout} {result.stderr}"
    loaded = verify_project_files(path)
    expected_name = "修改后" if stage == "manifest.replaced" else "旧版本"
    assert loaded["name"] == expected_name
    backup = path.with_suffix(".uipro.bak")
    if backup.exists():
        assert verify_project_files(backup)["name"] == "旧版本"
    assert (tmp_path / old["resources"][0]["path"]).read_bytes() == b"original-resource"


@pytest.mark.parametrize("stage", [
    "export.assets/value.bin.staged", "export.assets/value.bin.replaced",
    "export.ui_main.py.staged", "export.ui_main.py.replaced", "export.files_ready",
    "export.pointer.staged", "export.pointer.replaced",
])
def test_process_exit_never_mixes_export_generations(tmp_path: Path, stage: str) -> None:
    old_files = {"ui_main.py": b"old-ui", "assets/value.bin": b"old-resource"}
    publish_generation(tmp_path, old_files, expected_token=None)
    handlers = tmp_path / "handlers.py"
    handlers.write_text("# 用户业务代码\n", encoding="utf-8")
    result = crash("export", tmp_path, stage)
    assert result.returncode == 86, f"检查点未触发：{result.stdout} {result.stderr}"
    expected = ({"ui_main.py": b"new-ui", "assets/value.bin": b"new-resource"}
                if stage == "export.pointer.replaced" else old_files)
    assert read_generation(tmp_path) == expected
    assert handlers.read_text(encoding="utf-8") == "# 用户业务代码\n"


@pytest.mark.parametrize("destination", ["backup", "manifest"])
def test_replace_failure_preserves_current_project(
    project: Project, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination: str,
) -> None:
    path = tmp_path / "项目.uipro"
    receipt = commit_project(path, project, {}, expected_token=None)
    old_bytes = path.read_bytes()
    updated = deepcopy(project)
    updated["name"] = "未能保存"
    original_replace = os.replace
    failed_path = path if destination == "manifest" else path.with_suffix(".uipro.bak")

    def fail_replace(source: str | Path, target: str | Path) -> None:
        if Path(target) == failed_path:
            raise PermissionError("模拟文件替换被拒绝。")
        original_replace(source, target)

    monkeypatch.setattr(storage_probe.os, "replace", fail_replace)
    with pytest.raises(PermissionError):
        commit_project(path, updated, {}, expected_token=receipt.token)
    assert path.read_bytes() == old_bytes
    assert verify_project_files(path) == project


def test_external_change_is_not_overwritten(project: Project, tmp_path: Path) -> None:
    path = tmp_path / "项目.uipro"
    receipt = commit_project(path, project, {}, expected_token=None)
    external = b'{"external": true}'

    def alter(stage: str) -> None:
        if stage == "resources.ready":
            path.write_bytes(external)

    with pytest.raises(ContractError, match="磁盘文件发生变化"):
        commit_project(path, project, {}, expected_token=receipt.token, checkpoint=alter)
    assert path.read_bytes() == external


def test_missing_or_tampered_resource_does_not_commit(project: Project, tmp_path: Path) -> None:
    path = tmp_path / "项目.uipro"
    receipt = commit_project(path, project, {}, expected_token=None)
    updated, resources = with_resource(project, b"required-content")
    with pytest.raises(ContractError, match="缺少"):
        commit_project(path, updated, {}, expected_token=receipt.token)
    assert file_token(path) == receipt.token
    target = tmp_path / updated["resources"][0]["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"unexpected-content")
    with pytest.raises(ContractError, match="内容被修改"):
        commit_project(path, updated, resources, expected_token=receipt.token)
    assert file_token(path) == receipt.token


def test_recovery_copy_is_independent_of_original_directory(project: Project, tmp_path: Path) -> None:
    model, resources = with_resource(project, b"portable-content")
    original = tmp_path / "原目录" / "项目.uipro"
    recovery = tmp_path / "恢复目录" / "恢复副本.uipro"
    commit_project(original, model, resources, expected_token=None)
    commit_project(recovery, model, resources, expected_token=None)
    original.rename(original.with_suffix(".移走"))
    assert verify_project_files(recovery) == model


def test_export_rejects_business_file_and_parent_escape(tmp_path: Path) -> None:
    with pytest.raises(ContractError, match="不能覆盖"):
        publish_generation(tmp_path, {"ui_main.py": b"ui", "handlers.py": b"replace"}, expected_token=None)
    with pytest.raises(ContractError, match="相对路径"):
        publish_generation(tmp_path, {"ui_main.py": b"ui", "../escape.py": b"escape"}, expected_token=None)
    assert not (tmp_path / "current.json").exists()
    assert not (tmp_path / "handlers.py").exists()
