"""商业交付基础的回归：真实菜单、项目记录、布局与诊断内容。"""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Iterator
import zipfile

import pytest
from PySide6.QtCore import QPointF, QSettings
from PySide6.QtWidgets import QApplication

from app import diagnostics
from app.bootstrap import initialize
from app.main_window import MainWindow
from core.errors import DesignerError
from core.registry import WidgetRegistry
from core.storage import commit_project
from preview.service import PreviewService
from tests.test_storage import wait_for


@pytest.fixture
def window(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> Iterator[MainWindow]:
    initialize(qt_app, configure_logging=False)
    result = MainWindow(registry, enable_recovery=False,
                        settings=QSettings(str(tmp_path / "设置.ini"), QSettings.Format.IniFormat))
    result.show()
    qt_app.processEvents()
    try:
        yield result
    finally:
        result.discard_all_for_test()
        result.close()
        result.deleteLater()
        qt_app.processEvents()


def test_export_keeps_unsaved_state(window: MainWindow, tmp_path: Path) -> None:
    window.page.canvas.create_component("builtin.line_edit", QPointF(24, 32))
    state, cursor = window.document.state_id, window.document.history.cursor
    entry = window.export_python_to(tmp_path / "代码")
    assert entry.is_file() and window.document.dirty and window.document.path is None
    assert window.document.state_id == state and window.document.history.cursor == cursor
    assert window.actions["export_python"].shortcut().toString() == "Ctrl+Shift+E"
    assert entry.with_name("使用说明.md").is_file()


def test_business_code_name_can_be_selected(window: MainWindow) -> None:
    key = window.page.canvas.create_component("builtin.button", QPointF(24, 32))
    window.document.select(key)
    window.properties.refresh()
    editor = window.properties.editors["code_name"]
    assert editor.isEnabled() and editor.isReadOnly()
    editor.selectAll()
    assert editor.selectedText() == "button_1"


def test_recent_only_after_successful_save(window: MainWindow, tmp_path: Path, qt_app: QApplication) -> None:
    document = window.document
    target = tmp_path / "我的项目.uipro"
    window.save_service.save(document, target)
    assert window._recent_paths == []
    wait_for(lambda: not document.saving, qt_app)
    assert window._recent_paths == [str(target)]
    window.open_path(target)
    assert window._recent_paths == [str(target)]
    with pytest.raises(DesignerError):
        window.open_path(tmp_path / "不存在.uipro")
    assert window._recent_paths == [str(target)]
    window.clear_recent_projects()
    assert window.settings.value("files/recent") == []
    assert target.exists()


def test_recent_limit_and_settings(window: MainWindow, tmp_path: Path) -> None:
    for index in range(12):
        target = tmp_path / f"项目{index}.uipro"
        commit_project(target, window.document.model, expected_token=None)
        window.open_path(target)
    assert len(window._recent_paths) == 10
    assert window._recent_paths[0].endswith("项目11.uipro")
    assert window.settings.value("files/recent") == window._recent_paths


def test_restore_layout_recovers_closed_panels(window: MainWindow, qt_app: QApplication) -> None:
    window.toolbox_dock.hide()
    window.property_dock.hide()
    window.object_dock.setFloating(True)
    window.actions["restore_layout"].trigger()
    qt_app.processEvents()
    assert window.toolbox_dock.isVisible() and window.property_dock.isVisible()
    assert not window.object_dock.isFloating()


def test_geometry_is_restored(window: MainWindow, qt_app: QApplication) -> None:
    # 离屏平台会把恢复尺寸限制到虚拟屏幕，使用最小宽度验证保存的高度。
    window.resize(960, 700)
    qt_app.processEvents()
    window.settings.setValue("window/geometry", window.saveGeometry())
    second = MainWindow(window.registry, settings=window.settings, enable_recovery=False)
    try:
        assert second.geometry_restored
        assert second.size() == window.size()
    finally:
        second.discard_all_for_test()
        second.close()
        second.deleteLater()


def test_diagnostic_has_no_exception_message_or_project_text(tmp_path: Path) -> None:
    before = list(diagnostics._errors)
    try:
        try:
            raise ValueError("客户的私有项目内容")
        except ValueError:
            diagnostics.record_exception(*sys.exc_info())
        path = tmp_path / "诊断.zip"
        diagnostics.export_diagnostics(path, {"打开项目数": 1})
        with zipfile.ZipFile(path) as archive:
            assert set(archive.namelist()) == {"诊断.json", "说明.txt"}
            content = archive.read("诊断.json").decode("utf-8")
            assert "客户的私有项目内容" not in content and str(tmp_path) not in content
            report = json.loads(content)
            assert report["未处理异常摘要"][-1]["异常类型"] == "ValueError"
    finally:
        diagnostics._errors.clear()
        diagnostics._errors.extend(before)


def test_log_rotation_and_idempotence(tmp_path: Path) -> None:
    diagnostics.configure_file_logging(tmp_path)
    diagnostics.configure_file_logging(tmp_path)
    root = logging.getLogger()
    handlers = [handler for handler in root.handlers if getattr(handler, "_uiplay_file", False)]
    try:
        assert len(handlers) == 1 and isinstance(handlers[0], RotatingFileHandler)
        handler = handlers[0]
        handler.maxBytes = 300
        for index in range(30):
            logging.getLogger(__name__).info("轮转检查 %s %s", index, "中文信息" * 10)
        assert len(list(tmp_path.glob("设计器.log*"))) == 4
    finally:
        for handler in handlers:
            root.removeHandler(handler)
            handler.close()


def test_frozen_preview_uses_same_executable(qt_app: QApplication, registry: WidgetRegistry,
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    service = PreviewService(registry)
    assert service._command() == (sys.executable, ["--preview-worker"])
    service.deleteLater()
