"""覆盖生产存储服务的故障、锁、后台保存及恢复边界。"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from time import monotonic
from typing import Callable
from uuid import uuid4

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core import storage
from core.commands.nodes import set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import ProjectModel
from core.recovery import RecoveryService
from core.registry import WidgetRegistry
from core.save_service import SaveService
from core.storage import FileLease, commit_project, digest, file_token, load_project, resource_path


def wait_for(predicate: Callable[[], bool], application: QApplication, timeout: float = 5.0) -> None:
    deadline = monotonic() + timeout
    while not predicate() and monotonic() < deadline:
        application.processEvents()
        QTest.qWait(5)
    assert predicate(), "异步任务未能在规定时间内完成。"


@pytest.mark.parametrize("stage", ["asset.staged", "asset.replaced", "resources.ready", "backup.staged",
                                   "backup.replaced", "manifest.staged", "manifest.replaced"])
def test_process_crash_preserves_complete_project(project: ProjectModel, tmp_path: Path, stage: str) -> None:
    path = tmp_path / "中文项目.uipro"
    commit_project(path, project, expected_token=None)
    result = subprocess.run([sys.executable, "-X", "utf8", "-m", "tests.crash_worker", str(path), stage],
                            capture_output=True, text=True, encoding="utf-8", timeout=20, check=False)
    assert result.returncode == 86, result.stderr
    loaded = load_project(path).model
    assert loaded.name == ("新版本" if stage == "manifest.replaced" else project.name)
    for resource in loaded.data["resources"]:
        assert file_token(resource_path(path.parent, resource["path"], resource["sha256"])) == resource["sha256"]
    backup = path.with_suffix(".uipro.bak")
    if backup.exists():
        assert load_project(backup).model == project


@pytest.mark.parametrize("destination", ["backup", "manifest"])
def test_replace_failure_does_not_damage_old_file(project: ProjectModel, tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch, destination: str) -> None:
    path = tmp_path / "项目.uipro"
    token = commit_project(path, project, expected_token=None)
    original = os.replace

    def fail(source: Path, target: Path) -> None:
        failed = path.with_suffix(".uipro.bak") if destination == "backup" else path
        if target == failed:
            raise PermissionError("模拟拒绝替换。")
        original(source, target)

    monkeypatch.setattr(storage.os, "replace", fail)
    with pytest.raises(PermissionError):
        commit_project(path, replace(project, data=project.data.changed(name="未提交")), expected_token=token)
    assert load_project(path).model == project


def test_external_change_and_invalid_json_are_not_overwritten(project: ProjectModel, tmp_path: Path) -> None:
    path = tmp_path / "项目.uipro"
    token = commit_project(path, project, expected_token=None)

    def alter(stage: str) -> None:
        if stage == "resources.ready":
            path.write_bytes(b'{"outside": true}')

    with pytest.raises(DesignerError, match="磁盘项目发生变化"):
        commit_project(path, project, expected_token=token, checkpoint=alter)
    assert path.read_bytes() == b'{"outside": true}'
    for content in ('{"format":"uipro","format":"uipro"}', '{"value":NaN}', '损坏文件'):
        path.write_text(content, encoding="utf-8")
        with pytest.raises(DesignerError):
            load_project(path)


@pytest.mark.parametrize("existing", [False, True])
def test_save_never_creates_project_that_exceeds_read_limit(project: ProjectModel, tmp_path: Path,
                                                          monkeypatch: pytest.MonkeyPatch, existing: bool) -> None:
    path = tmp_path / "容量边界.uipro"
    token = commit_project(path, project, expected_token=None) if existing else None
    original = path.read_bytes() if existing else None
    monkeypatch.setattr(storage, "MAX_PROJECT_BYTES", len(project.to_bytes()) + 8, raising=False)
    oversized = replace(project, data=project.data.changed(name="超出容量的项目名称" * 100))
    stages: list[str] = []
    with pytest.raises(DesignerError, match="项目.*超过"):
        commit_project(path, oversized, expected_token=token, checkpoint=stages.append)
    assert not stages, "容量检查必须发生在资源、备份和项目写入之前。"
    assert not path.with_suffix(".uipro.bak").exists()
    if existing:
        assert path.read_bytes() == original and load_project(path).model == project
    else:
        assert not path.exists()


def test_read_limit_uses_actual_byte_count(project: ProjectModel, tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "读取容量.uipro"
    payload = project.to_bytes()
    path.write_bytes(payload)
    monkeypatch.setattr(storage, "MAX_PROJECT_BYTES", len(payload), raising=False)
    assert load_project(path).model == project
    monkeypatch.setattr(storage, "MAX_PROJECT_BYTES", len(payload) - 1)
    with pytest.raises(DesignerError, match="超过"):
        load_project(path)


def test_resource_copy_is_independent_and_missing_resource_fails(project: ProjectModel, tmp_path: Path) -> None:
    source = tmp_path / "来源"
    payload = b"portable-resource"
    checksum = digest(payload)
    relative = f"assets/{checksum}.bin"
    resource = source / relative
    resource.parent.mkdir(parents=True)
    resource.write_bytes(payload)
    project = replace(project, data=project.data.changed(resources=[{
        "id": str(uuid4()), "name": "图片", "kind": "binary", "path": relative, "sha256": checksum,
    }]))
    target = tmp_path / "恢复" / "项目.uipro"
    commit_project(target, project, expected_token=None, resource_source=source)
    source.rename(tmp_path / "原来源已移动")
    assert (target.parent / relative).read_bytes() == payload
    with pytest.raises(DesignerError, match="缺失"):
        commit_project(tmp_path / "另一处" / "项目.uipro", project, expected_token=None, resource_source=source)


def test_lock_excludes_second_writer(tmp_path: Path) -> None:
    path = tmp_path / "项目.uipro"
    first, second = FileLease(path), FileLease(path)
    try:
        assert first.acquired and not second.acquired
    finally:
        first.release()
        second.release()
    third = FileLease(path)
    assert third.acquired
    third.release()


def test_async_save_uses_captured_state(project: ProjectModel, registry: WidgetRegistry,
                                      qt_app: QApplication, tmp_path: Path) -> None:
    document = DocumentSession(project, registry)
    service = SaveService()
    try:
        service.save(document, tmp_path / "保存.uipro")
        document.execute("后续编辑", lambda model: set_property(model, registry, model.root_id, "window_title", "新编辑"))
        wait_for(lambda: not document.saving, qt_app)
        assert load_project(document.path).model == project
        assert document.dirty
        document.undo()
        assert not document.dirty
    finally:
        service.shutdown()


@pytest.mark.parametrize("existing", [False, True])
def test_async_capacity_failure_preserves_state_and_allows_retry(project: ProjectModel, registry: WidgetRegistry,
                                                               qt_app: QApplication, tmp_path: Path,
                                                               monkeypatch: pytest.MonkeyPatch, existing: bool) -> None:
    document = DocumentSession(project, registry)
    service = SaveService()
    target = tmp_path / "容量失败后重试.uipro"
    results: list[tuple[bool, str]] = []
    service.finished.connect(lambda document, success, message: results.append((success, message)))
    try:
        if existing:
            service.save(document, target)
            wait_for(lambda: not document.saving, qt_app)
            service.save(document, target)
            wait_for(lambda: not document.saving, qt_app)
        disk_before = {path.name: path.read_bytes() for path in tmp_path.glob("*.uipro*")
                       if path.suffix != ".lock"}
        saved_state = (document.path, document.disk_token, document.resource_base)
        document.execute("增大项目内容", lambda model: set_property(
            model, registry, model.root_id, "window_title", "容量边界检查" * 100))
        edited, cursor = document.model, document.history.cursor
        with monkeypatch.context() as patch:
            patch.setattr(storage, "MAX_PROJECT_BYTES", len(project.to_bytes()) + 8)
            service.save(document, target)
            wait_for(lambda: not document.saving, qt_app)
        assert results[-1][0] is False and "超过" in results[-1][1]
        assert document.dirty and document.model == edited and document.history.cursor == cursor
        assert (document.path, document.disk_token, document.resource_base) == saved_state
        assert not service._jobs
        assert {path.name: path.read_bytes() for path in tmp_path.glob("*.uipro*")
                if path.suffix != ".lock"} == disk_before
        competing = FileLease(target)
        try:
            assert competing.acquired is not existing
        finally:
            competing.release()
        service.save(document, target)
        wait_for(lambda: not document.saving, qt_app)
        assert results[-1][0] is True and not document.dirty
        assert load_project(target).model == edited
        if existing:
            assert load_project(target.with_suffix(".uipro.bak")).model == project
    finally:
        service.shutdown()


def test_capacity_failure_does_not_touch_resources_or_existing_backup(project: ProjectModel, tmp_path: Path,
                                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "目标" / "项目.uipro"
    token = commit_project(path, project, expected_token=None)
    saved = replace(project, data=project.data.changed(name="已经保存的修改"))
    token = commit_project(path, saved, expected_token=token)
    before = {item.name: item.read_bytes() for item in path.parent.iterdir()}
    payload = b"capacity-resource"
    checksum = digest(payload)
    relative = f"assets/{checksum}.bin"
    source = tmp_path / "来源"
    resource = source / relative
    resource.parent.mkdir(parents=True)
    resource.write_bytes(payload)
    oversized = replace(saved, data=saved.data.changed(name="超过容量" * 100, resources=[{
        "id": str(uuid4()), "name": "容量检查图片", "kind": "binary", "path": relative, "sha256": checksum,
    }]))
    monkeypatch.setattr(storage, "MAX_PROJECT_BYTES", len(saved.to_bytes()) + 8)
    with pytest.raises(DesignerError, match="超过"):
        commit_project(path, oversized, expected_token=token, resource_source=source)
    assert not (path.parent / "assets").exists()
    assert {item.name: item.read_bytes() for item in path.parent.iterdir()} == before
    assert load_project(path.with_suffix(".uipro.bak")).model == project


def test_recovery_snapshot_is_committed_data_only(project: ProjectModel, registry: WidgetRegistry,
                                                 qt_app: QApplication, tmp_path: Path) -> None:
    document = DocumentSession(project, registry)
    service = RecoveryService(tmp_path / "恢复副本")
    try:
        service.watch(document)
        service.flush_due(force=True)
        wait_for(lambda: bool(service.discover(include_active=True)), qt_app)
        assert load_project(service.discover(include_active=True)[0]).model == project
        assert service.discover() == []
        wait_for(lambda: not service._watches[document.session_id].running, qt_app)
        service.dismiss(document)
        assert not service.discover()
    finally:
        service.shutdown()


def test_successful_save_archives_old_recovery_but_new_edits_recover(project: ProjectModel, registry: WidgetRegistry,
                                                                  qt_app: QApplication, tmp_path: Path) -> None:
    document = DocumentSession(project, registry)
    service = RecoveryService(tmp_path / "恢复副本")
    try:
        service.watch(document)
        service.flush_due(force=True)
        wait_for(lambda: not service._watches[document.session_id].running, qt_app)
        assert service.discover(include_active=True)
        target = tmp_path / "保存.uipro"
        ticket = document.begin_save(target, None)
        token = commit_project(target, ticket.model, expected_token=None)
        document.finish_save(ticket, success=True, token=token)
        service.mark_saved(document)
        assert not service.discover(include_active=True)
        document.execute("再次编辑", lambda model: set_property(model, registry, model.root_id, "window_title", "新修改"))
        service.flush_due(force=True)
        wait_for(lambda: not service._watches[document.session_id].running, qt_app)
        recovered = load_project(service.discover(include_active=True)[0]).model
        assert recovered.nodes[recovered.root_id].properties["window_title"] == "新修改"
        service.dismiss(document)
    finally:
        service.shutdown()


def test_oversized_json_integer_reports_domain_error(tmp_path: Path) -> None:
    path = tmp_path / "无效数值.uipro"
    path.write_text('{"schema_version":' + "9" * 5000 + "}", encoding="utf-8")
    with pytest.raises(DesignerError, match="无法读取"):
        load_project(path)


def test_disappearing_recovery_record_does_not_abort_discovery(project: ProjectModel, tmp_path: Path,
                                                              qt_app: QApplication,
                                                              monkeypatch: pytest.MonkeyPatch) -> None:
    service = RecoveryService(tmp_path / "恢复记录")
    present = service.directory / "项目" / "存在" / "snapshot.uipro"
    healthy = service.directory / "项目" / "正常" / "snapshot.uipro"
    commit_project(present, project, expected_token=None)
    commit_project(healthy, project, expected_token=None)
    original_stat = Path.stat
    original_glob = Path.glob

    def disappearing_stat(path: Path, *args: object, **kwargs: object) -> object:
        if path == present:
            raise FileNotFoundError(2, "模拟扫描过程中另一个窗口归档了恢复记录。")
        return original_stat(path, *args, **kwargs)

    try:
        monkeypatch.setattr(Path, "stat", disappearing_stat)
        monkeypatch.setattr(Path, "glob", lambda directory, pattern: iter((present, healthy))
                            if directory == service.directory else original_glob(directory, pattern))
        assert service.discover(include_active=True) == [healthy]
    finally:
        service.shutdown()
