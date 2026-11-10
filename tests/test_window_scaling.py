"""窗口级跟随开关的模型、拖动、嵌套容器、预览和独立导出验证。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QCheckBox

from app.main_window import MainWindow
from codegen.publisher import export_project
from core.build_plan import compile_plan, preview_window_resize
from core.commands.nodes import create_node, resize_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.hierarchy import absolute_position, content_size, pages
from core.models import ProjectModel, Rect
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from core.window_scaling import scale_base_size
from designer.canvas import DesignerCanvas
from layout.scaling import ScaleItem, scale_layout
from runtime.builder import RuntimeTree
from tests.test_clipboard import window
from tests.test_codegen import load_export


def build_model(project: ProjectModel, registry: WidgetRegistry, enabled: bool = True) -> tuple[ProjectModel, dict[str, str]]:
    keys: dict[str, str] = {}
    for kind, x, y in (("button", 40, 360), ("group_box", 40, 40), ("tab_widget", 400, 40),
                       ("tool_bar", 0, 0), ("status_bar", 0, 0), ("timer", 0, 0)):
        project, keys[kind] = create_node(project, registry, "builtin." + kind, x, y)
    project, keys["inner"] = create_node(project, registry, "builtin.line_edit", 16, 32, parent_id=keys["group_box"])
    first, second = pages(project, keys["tab_widget"])
    project, keys["first"] = create_node(project, registry, "builtin.label", 16, 24, parent_id=first.id)
    project, keys["second"] = create_node(project, registry, "builtin.button", 40, 40, parent_id=second.id)
    project = set_property(project, registry, keys["button"], "font_size", 18)
    project = set_property(project, registry, project.root_id, "scale_children", enabled)
    registry.validate(project)
    return project, keys


def test_switch_is_only_in_window_properties_and_does_not_move_controls(window: MainWindow, qt_app: QApplication) -> None:
    canvas, document = window.page.canvas, window.document
    key = canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    assert "scale_children" not in window.properties.editors
    window.select_window()
    qt_app.processEvents()
    checkbox = window.properties.editors["scale_children"]
    assert isinstance(checkbox, QCheckBox) and not checkbox.isChecked()
    before, cursor = document.model.nodes[key].geometry, document.history.cursor
    checkbox.click()
    qt_app.processEvents()
    assert document.model.nodes[document.model.root_id].properties["scale_children"] is True
    assert document.model.nodes[key].geometry == before and document.history.cursor == cursor + 1
    document.undo()
    qt_app.processEvents()
    assert not window.properties.editors["scale_children"].isChecked()


@pytest.mark.parametrize("enabled", [False, True])
def test_model_resize_and_undo_are_atomic(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication, enabled: bool) -> None:
    project, keys = build_model(project, registry, enabled)
    document = DocumentSession(project, registry, saved=True)
    before = project.nodes[project.root_id].geometry
    document.execute("调整窗口", lambda model: resize_node(model, model.root_id, replace(before, width=1200, height=808)))
    button = document.model.nodes[keys["button"]].geometry
    assert button == (Rect(60, 540, 180, 60) if enabled else project.nodes[keys["button"]].geometry)
    assert document.history.cursor == 1
    assert document.model.nodes[keys["button"]].properties["font_size"] == 18
    for kind in ("timer", "tool_bar", "status_bar"):
        assert document.model.nodes[keys[kind]] == project.nodes[keys[kind]]
    document.undo()
    assert document.model == project and not document.dirty
    document.redo()
    assert document.model.nodes[keys["button"]].geometry == button


def test_width_height_properties_follow_but_screen_position_does_not(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = build_model(project, registry)
    old = project.nodes[keys["button"]].geometry
    wider = set_property(project, registry, project.root_id, "geometry.width", 1600)
    assert wider.nodes[keys["button"]].geometry == Rect(old.x * 2, old.y, old.width * 2, old.height)
    taller = set_property(project, registry, project.root_id, "geometry.height", 1056)
    assert taller.nodes[keys["button"]].geometry == Rect(old.x, old.y * 2, old.width, old.height * 2)
    moved = set_property(project, registry, project.root_id, "geometry.x", 500)
    assert moved.nodes[keys["button"]].geometry == old
    resized_group = resize_node(project, keys["group_box"], replace(project.nodes[keys["group_box"]].geometry, width=500))
    assert resized_group.nodes[keys["inner"]].geometry == project.nodes[keys["inner"]].geometry


@pytest.mark.parametrize("enabled", [False, True])
def test_preview_and_export_match_nested_model_after_resize(project: ProjectModel, registry: WidgetRegistry,
                                                          qt_app: QApplication, tmp_path: Path, enabled: bool) -> None:
    project, keys = build_model(project, registry, enabled)
    tree = RuntimeTree(registry, design_mode=False)
    tree.apply(compile_plan(project, registry, "缩放检查"))
    exported = load_export(export_project(project, registry, tmp_path), qt_app)
    try:
        tree.root.show()
        exported.show()
        qt_app.processEvents()
        tree.root.resize(1200, 808)
        exported.resize(1200, 808)
        qt_app.processEvents()
        candidate = resize_node(project, project.root_id, replace(project.nodes[project.root_id].geometry, width=1200, height=808))
        for node in candidate.nodes.values():
            if node.slot != "children":
                continue
            native = tree.widgets[node.id]
            actual = exported.controls[node.code_name]
            assert actual.geometry() == native.geometry(), node.name
            assert (native.width(), native.height()) == (node.geometry.width, node.geometry.height), node.name
            assert native.mapTo(tree.root, QPoint()) == QPoint(*absolute_position(candidate, node.id)), node.name
            assert actual.mapTo(exported, QPoint()) == QPoint(*absolute_position(candidate, node.id)), node.name
        assert tree.widgets[keys["button"]].font().pointSize() == 18
        assert tree.widgets[keys["tool_bar"]].height() == 36 and tree.widgets[keys["status_bar"]].height() == 28
        assert not tree.widgets[keys["second"]].isVisible()
        assert project.nodes[keys["button"]].geometry == Rect(40, 360, 120, 40)
    finally:
        tree.dispose()
        exported.close()
        exported.deleteLater()


def test_repeated_runtime_resize_has_no_rounding_drift(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    project, keys = build_model(project, registry)
    tree = RuntimeTree(registry, design_mode=False)
    tree.apply(compile_plan(project, registry, "缩放基准"))
    try:
        tree.root.show()
        qt_app.processEvents()
        original = {key: widget.geometry() for key, widget in tree.widgets.items() if project.nodes[key].slot in {"children", "pages"}}
        for width, height in [(613, 449), (1257, 847), (400, 320), (803, 567), (800, 560)] * 4:
            tree.root.resize(width, height)
            qt_app.processEvents()
        assert all(tree.widgets[key].geometry() == rect for key, rect in original.items())
        assert tree.scaler is not None and not tree.scaler._failed
        disabled = set_property(project, registry, project.root_id, "scale_children", False)
        old_scaler = tree.scaler
        tree.apply(compile_plan(disabled, registry, "关闭跟随"))
        assert old_scaler._disposed and tree.scaler is None
        tree.root.resize(1200, 808)
        qt_app.processEvents()
        assert tree.widgets[keys["button"]].geometry() == original[keys["button"]]
    finally:
        tree.dispose()


@pytest.mark.parametrize("cancel", [False, True])
def test_canvas_root_drag_follows_live_and_can_cancel(project: ProjectModel, registry: WidgetRegistry,
                                                    qt_app: QApplication, cancel: bool) -> None:
    project, keys = build_model(project, registry)
    document = DocumentSession(project, registry, saved=True)
    canvas = DesignerCanvas(document)
    try:
        canvas.resize(1250, 950)
        canvas.show()
        qt_app.processEvents()
        document.select(project.root_id)
        point = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        target = point + QPoint(160, 80)
        event = QMouseEvent(QEvent.Type.MouseMove, QPointF(target), QPointF(canvas.viewport().mapToGlobal(target)),
                            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(canvas.viewport(), event)
        assert canvas._resize is not None and canvas._resize.preview_applied
        assert document.model == project and not document.dirty
        assert canvas.renderer.tree.widgets[keys["button"]].width() == 144
        if cancel:
            QTest.keyClick(canvas, Qt.Key.Key_Escape)
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        if cancel:
            assert document.model == project and document.history.cursor == 0
            assert canvas.renderer.tree.widgets[keys["button"]].width() == 120
        else:
            assert document.history.cursor == 1 and document.model.nodes[keys["button"]].geometry.width == 144
            document.undo()
            assert document.model == project
            assert canvas.renderer.tree.widgets[keys["button"]].width() == 120
    finally:
        canvas.dispose()
        canvas.close()


def test_saved_switch_and_isolated_export_resize(project: ProjectModel, registry: WidgetRegistry,
                                               qt_app: QApplication, tmp_path: Path) -> None:
    project, keys = build_model(project, registry)
    path = tmp_path / "跟随窗口.uipro"
    commit_project(path, project, expected_token=None)
    assert load_project(path).model == project
    entry = export_project(project, registry, tmp_path / "独立导出")
    code = '''import importlib.util,sys
from PySide6.QtWidgets import QApplication
app=QApplication([])
spec=importlib.util.spec_from_file_location('entry',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
window=module.create_window(app)
window.show()
app.processEvents()
window.resize(1200,808)
app.processEvents()
button=window.controls['button_1']
assert (button.x(),button.y(),button.width(),button.height()) == (60,540,180,60)
assert button.font().pointSize()==18
window.resize(800,560)
app.processEvents()
assert (button.x(),button.y(),button.width(),button.height()) == (40,360,120,40)
window.close()
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(entry)], cwd=tmp_path,
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stderr


def test_small_window_preserves_container_minimum_and_unknown_switch_rejected(project: ProjectModel, registry: WidgetRegistry,
                                                                           qt_app: QApplication) -> None:
    project, keys = build_model(project, registry)
    small = resize_node(project, project.root_id, replace(project.nodes[project.root_id].geometry, width=80, height=100))
    registry.validate(small)
    assert small.nodes[keys["tab_widget"]].geometry.width >= 64
    assert small.nodes[keys["group_box"]].geometry.width >= 25
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError):
        document.execute("非法开关值", lambda model: set_property(model, registry, model.root_id, "scale_children", "开启"))
    assert document.model == project and document.history.cursor == 0


def test_shared_edge_rounding_and_same_size_identity() -> None:
    items = (ScaleItem("central", None, "central", None),
             ScaleItem("left", "central", "children", (17, 10, 34, 20)),
             ScaleItem("right", "central", "children", (51, 10, 37, 20)))
    result = scale_layout(items, (100, 100), (133, 175))
    assert result["left"][0] + result["left"][2] == result["right"][0]
    assert scale_layout(items, (100, 100), (100, 100))["left"] == items[1].rect


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("size", [(80, 100), (400, 320), (613, 449), (800, 560), (1200, 808), (16384, 16384)])
def test_resize_preview_plan_matches_full_compilation(project: ProjectModel, registry: WidgetRegistry,
                                                      enabled: bool, size: tuple[int, int]) -> None:
    project, keys = build_model(project, registry, enabled)
    project = set_property(project, registry, keys["group_box"], "content_left", 17)
    source = compile_plan(project, registry, "固定基准")
    root = project.nodes[project.root_id].geometry
    geometry = replace(root, width=size[0], height=size[1])
    candidate = resize_node(project, project.root_id, geometry)
    preview = preview_window_resize(source, geometry)
    assert preview == compile_plan(candidate, registry, "固定基准")
    assert source.nodes[0].geometry == root
    assert all(before.properties is after.properties for before, after in zip(source.nodes, preview.nodes))


def test_resize_preview_rejects_invalid_geometry_and_exhausted_content(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, _ = build_model(project, registry)
    source = compile_plan(project, registry, "固定基准")
    root = project.nodes[project.root_id].geometry
    for geometry in (replace(root, width=0), replace(root, height=64), replace(root, x=root.x + 1)):
        with pytest.raises(DesignerError):
            preview_window_resize(source, geometry)


def test_resize_gesture_reuses_properties_without_full_compile(project: ProjectModel, registry: WidgetRegistry,
                                                             qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    from designer import canvas as canvas_module

    project, _ = build_model(project, registry)
    document = DocumentSession(project, registry, saved=True)
    canvas = DesignerCanvas(document)
    errors: list[str] = []
    canvas.error.connect(errors.append)
    try:
        canvas.resize(1250, 950)
        canvas.show()
        qt_app.processEvents()
        document.select(project.root_id)
        point = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)

        def reject_compile(*args: object, **kwargs: object) -> None:
            raise AssertionError("临时拉伸不应重新编译未变化的属性。")

        with monkeypatch.context() as patch:
            patch.setattr(canvas_module, "compile_plan", reject_compile)
            for delta in (QPoint(160, 80), QPoint(63, 47), QPoint(0, 0)):
                target = point + delta
                event = QMouseEvent(QEvent.Type.MouseMove, QPointF(target), QPointF(canvas.viewport().mapToGlobal(target)),
                                    Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(canvas.viewport(), event)
                assert not errors and document.model == project and document.history.cursor == 0
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        assert document.model == project and document.history.cursor == 0
    finally:
        canvas.dispose()
        canvas.close()


@pytest.mark.parametrize("fail", [False, True])
def test_resize_release_reuses_preview_or_restores_after_failure(project: ProjectModel, registry: WidgetRegistry,
                                                              qt_app: QApplication, monkeypatch: pytest.MonkeyPatch,
                                                              fail: bool) -> None:
    project, keys = build_model(project, registry)
    document = DocumentSession(project, registry, saved=True)
    canvas = DesignerCanvas(document)
    errors: list[str] = []
    canvas.error.connect(errors.append)
    try:
        canvas.resize(1250, 950)
        canvas.show()
        qt_app.processEvents()
        document.select(project.root_id)
        point = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        target = point + QPoint(160, 80)
        event = QMouseEvent(QEvent.Type.MouseMove, QPointF(target), QPointF(canvas.viewport().mapToGlobal(target)),
                            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(canvas.viewport(), event)
        assert canvas.renderer.tree.widgets[keys["button"]].width() == 144
        renders: list[str] = []
        original = canvas.renderer.tree.image

        def image(key: str, ratio: float) -> object:
            renders.append(key)
            return original(key, ratio)

        def reject(*args: object, **kwargs: object) -> None:
            raise DesignerError("模拟提交时校验失败。")

        monkeypatch.setattr(canvas.renderer.tree, "image", image)
        if fail:
            monkeypatch.setattr(document, "execute", reject)
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        assert canvas._resize is None
        if fail:
            assert document.model == project and document.history.cursor == 0
            assert canvas.renderer.tree.widgets[keys["button"]].width() == 120
            assert errors == ["模拟提交时校验失败。"]
        else:
            assert document.history.cursor == 1 and not errors
            assert not renders, "已画好的缩放结果不应在提交时还原并重复绘制。"
    finally:
        canvas.dispose()
        canvas.close()


def test_geometry_change_preserves_images_and_parent_font_still_invalidates(project: ProjectModel, registry: WidgetRegistry,
                                                                          qt_app: QApplication) -> None:
    project, keys = build_model(project, registry, enabled=False)
    document = DocumentSession(project, registry, saved=True)
    canvas = DesignerCanvas(document)
    try:
        before = canvas.renderer.items[keys["first"]].pixmap().cacheKey()
        root = project.nodes[project.root_id].geometry
        document.execute("只扩大窗口", lambda model: resize_node(model, model.root_id, replace(root, width=1200, height=808)))
        assert canvas.renderer.items[keys["first"]].pixmap().cacheKey() == before
        for key in (keys["tool_bar"], keys["status_bar"]):
            widget = canvas.renderer.tree.widgets[key]
            assert canvas.renderer.items[key].pixmap().width() == round(widget.width() * canvas.renderer.ratio)
        document.execute("改变继承字体", lambda model: set_property(model, registry, model.root_id, "font_size", 24))
        assert canvas.renderer.items[keys["first"]].pixmap().cacheKey() != before
        assert canvas.renderer.tree.widgets[keys["first"]].font().pointSize() == 24
    finally:
        canvas.dispose()
        canvas.close()
