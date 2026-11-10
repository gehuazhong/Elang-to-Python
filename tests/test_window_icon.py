"""窗口图标的导入、撤销、标题栏绘制、项目保存及独立导出回归。"""

from __future__ import annotations

from pathlib import Path
import shutil
import struct
import subprocess
import sys

import pytest
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter
from PySide6.QtWidgets import QApplication, QFileDialog, QStyleOptionGraphicsItem

from app.main_window import MainWindow
from codegen.generator import generate_files
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.models import ProjectModel
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from panels.image_editor import ImageEditor, import_image
from runtime.easy_widgets import decoded_image
from runtime.preview import PreviewRuntime
from tests.test_appearance import designed_window
from tests.test_codegen import load_export


ICON_COLOR = QColor("#287e59")


def png_bytes(size: int, color: QColor) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    try:
        painter.fillRect(size // 4, size // 4, size // 2, size // 2, color)
    finally:
        painter.end()
    buffer = QBuffer()
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    return bytes(buffer.data())


@pytest.fixture
def icon_file(tmp_path: Path) -> Path:
    entries: list[bytes] = []
    images: list[bytes] = []
    offset = 6 + 3 * 16
    for size, color in ((16, QColor("#dd6633")), (64, ICON_COLOR), (32, QColor("#2255dd"))):
        payload = png_bytes(size, color)
        entries.append(struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(payload), offset))
        images.append(payload)
        offset += len(payload)
    path = tmp_path / "中文 程序图标.ico"
    path.write_bytes(struct.pack("<HHH", 0, 1, len(entries)) + b"".join(entries + images))
    return path


def assert_icon(icon: QIcon) -> None:
    assert not icon.isNull()
    picture = icon.pixmap(64, 64).toImage()
    assert picture.pixelColor(picture.width() // 2, picture.height() // 2) == ICON_COLOR
    assert picture.pixelColor(0, 0).alpha() == 0


@pytest.mark.parametrize("format", ["ico", "png"])
def test_import_preserves_transparency_and_best_icon_frame(icon_file: Path, format: str) -> None:
    if format == "png":
        icon_file = icon_file.with_suffix(".png")
        icon_file.write_bytes(png_bytes(64, ICON_COLOR))
    value = import_image(icon_file, icon=True)
    icon_file.unlink()
    picture = decoded_image(value)
    assert picture.size().toTuple() == (64, 64)
    assert picture.pixelColor(32, 32) == ICON_COLOR
    assert picture.pixelColor(0, 0).alpha() == 0


def test_property_selection_paints_titlebar_and_supports_clear_undo_redo(
    designed_window: MainWindow, qt_app: QApplication, icon_file: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = designed_window
    document, panel = window.document, window.properties
    editor = panel.editors["window_icon"]
    assert isinstance(editor, ImageEditor) and editor.icon_mode
    assert editor.accessibleName() == "程序图标" and not editor.clear_button.isEnabled()
    spec = window.registry.require("builtin.main_window").property("window_icon")
    assert spec.group == "窗口" and spec.label == "程序图标"

    def choose(dialog: QFileDialog) -> int:
        assert editor.choosing and dialog.windowTitle() == "选择程序图标"
        assert "*.ico" in dialog.nameFilters()[0] and "*.png" in dialog.nameFilters()[0]
        dialog.selectFile(str(icon_file))
        return QFileDialog.DialogCode.Accepted

    monkeypatch.setattr(QFileDialog, "exec", choose)
    cursor = document.history.cursor
    editor.button.click()
    qt_app.processEvents()
    assert document.history.cursor == cursor + 1
    frame = window.page.canvas.renderer.frame
    assert_icon(window.page.canvas.renderer.tree.root.windowIcon())
    assert_icon(frame.icon)
    for ratio in (1, 2):
        rendered = QImage(64 * ratio, 44 * ratio, QImage.Format.Format_ARGB32)
        rendered.setDevicePixelRatio(ratio)
        rendered.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rendered)
        try:
            painter.translate(0, 39)
            frame.paint(painter, QStyleOptionGraphicsItem())
        finally:
            painter.end()
        assert rendered.pixelColor(18 * ratio, 19 * ratio) == ICON_COLOR
    panel.editors["window_icon"].clear_button.click()
    qt_app.processEvents()
    assert document.history.cursor == cursor + 2
    assert window.page.canvas.renderer.tree.root.windowIcon().isNull()
    assert frame.icon.isNull()
    document.undo()
    qt_app.processEvents()
    assert_icon(frame.icon)
    assert panel.editors["window_icon"].clear_button.isEnabled()
    document.redo()
    qt_app.processEvents()
    assert frame.icon.isNull() and not panel.editors["window_icon"].clear_button.isEnabled()


@pytest.mark.parametrize("outcome", ["cancel", "broken", "oversized"])
def test_cancel_or_bad_import_preserves_existing_icon(
    designed_window: MainWindow, qt_app: QApplication, icon_file: Path,
    monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    document, panel = designed_window.document, designed_window.properties
    value = import_image(icon_file, icon=True)
    document.execute("设置图标", lambda model: set_property(model, document.registry, model.root_id, "window_icon", value))
    qt_app.processEvents()
    original, cursor = document.model, document.history.cursor
    errors: list[str] = []
    panel.error.connect(errors.append)
    path = icon_file.with_suffix(".png")
    if outcome == "oversized":
        image = QImage(4097, 1, QImage.Format.Format_ARGB32)
        image.fill(ICON_COLOR)
        assert image.save(str(path))
    else:
        path.write_bytes(b"invalid image")

    def choose(dialog: QFileDialog) -> int:
        dialog.selectFile(str(path))
        return QFileDialog.DialogCode.Rejected if outcome == "cancel" else QFileDialog.DialogCode.Accepted

    monkeypatch.setattr(QFileDialog, "exec", choose)
    panel.editors["window_icon"].button.click()
    qt_app.processEvents()
    assert document.model == original and document.history.cursor == cursor
    assert bool(errors) == (outcome != "cancel")
    assert not panel.editors["window_icon"].choosing
    assert_icon(designed_window.page.canvas.renderer.frame.icon)


@pytest.mark.parametrize("border", ["standard", "fixed", "none"])
def test_saved_icon_matches_preview_and_export_without_original_file(
    project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication,
    tmp_path: Path, icon_file: Path, border: str,
) -> None:
    value = import_image(icon_file, icon=True)
    project = set_property(project, registry, project.root_id, "window_icon", value)
    project = set_property(project, registry, project.root_id, "border_style", border)
    project, picture = create_node(project, registry, "builtin.picture_box", 24, 24)
    project = set_property(project, registry, picture, "image", value)
    path = tmp_path / "保存图标.uipro"
    commit_project(path, project, expected_token=None)
    icon_file.unlink()
    loaded = load_project(path).model
    assert loaded == project
    files = generate_files(loaded, registry)
    assert len([name for name in files if name.startswith("assets/")]) == 1
    assert value.encode("ascii") not in files["ui_main.py"]
    preview = PreviewRuntime(registry)
    generated = load_export(export_project(loaded, registry, tmp_path / "导出目录"), qt_app)
    try:
        preview.show(compile_plan(loaded, registry, "图标预览"), loaded)
        assert_icon(preview.tree.root.windowIcon())
        assert_icon(generated.windowIcon())
        assert preview.tree.root.windowFlags() == generated.windowFlags()
        cleared = set_property(loaded, registry, loaded.root_id, "window_icon", "")
        preview.show(compile_plan(cleared, registry, "清除图标"), cleared)
        assert preview.tree.root.windowIcon().isNull()
    finally:
        preview.dispose()
        generated.close()
        generated.deleteLater()


def test_exported_icon_survives_directory_move_and_runs_without_designer(
    project: ProjectModel, registry: WidgetRegistry, tmp_path: Path, icon_file: Path,
) -> None:
    value = import_image(icon_file, icon=True)
    project = set_property(project, registry, project.root_id, "window_icon", value)
    entry = export_project(project, registry, tmp_path / "原导出目录")
    moved = tmp_path / "移动后 中文目录"
    shutil.copytree(entry.parent, moved)
    icon_file.unlink()
    code = '''import importlib.util, sys
from PySide6.QtWidgets import QApplication
spec = importlib.util.spec_from_file_location("exported_entry", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
application = QApplication([])
window = module.create_window(application)
icon = window.windowIcon()
assert not icon.isNull()
image = icon.pixmap(64, 64).toImage()
assert image.pixelColor(32, 32).name() == "#287e59"
assert image.pixelColor(0, 0).alpha() == 0
assert not any(name in sys.modules for name in ("app", "core", "runtime"))
window.close()
print("独立图标检查通过")
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(moved / "main.py")],
                            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "独立图标检查通过" in result.stdout


def test_legacy_project_without_icon_keeps_default(
    project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication, tmp_path: Path,
) -> None:
    assert "window_icon" not in project.nodes[project.root_id].properties
    path = tmp_path / "旧项目.uipro"
    commit_project(path, project, expected_token=None)
    loaded = load_project(path).model
    assert "window_icon" not in loaded.nodes[loaded.root_id].properties
    assert compile_plan(loaded, registry, "旧项目图标").nodes[0].properties["window_icon"] == ""
    generated = load_export(export_project(loaded, registry, tmp_path / "旧项目导出"), qt_app)
    try:
        assert generated.windowIcon().isNull()
    finally:
        generated.close()
        generated.deleteLater()
