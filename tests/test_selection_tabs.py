"""选择夹的四向表头、内容坐标、页签操作及独立导出。"""

from dataclasses import replace

import pytest
from PySide6.QtCore import QPoint, QPointF, QSize, Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QTabBar

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import create_node, delete_node, set_property
from core.document import DocumentSession
from core.hierarchy import absolute_position, content_size, pages
from core.storage import commit_project, load_project
from designer.canvas import DesignerCanvas
from panels.properties import PropertyPanel
from runtime.builder import RuntimeTree, verify_registry
from tests.test_codegen import load_export
from tests.test_easy_widgets import image_value


def tab_model(project, registry, **options):
    project, tab = create_node(project, registry, "builtin.tab_widget", 40, 40)
    for key, value in options.items():
        project = set_property(project, registry, tab, key, value)
    first, second = pages(project, tab)
    project, child = create_node(project, registry, "builtin.button", 16, 40, parent_id=first.id)
    return project, tab, first.id, second.id, child


@pytest.mark.parametrize("position", ["top", "bottom", "left", "right"])
@pytest.mark.parametrize("visible", [True, False])
def test_page_geometry_save_export_and_canvas_click(project, registry, qt_app, tmp_path, position, visible):
    model, tab, first, second, child = tab_model(project, registry, tab_position=position, header_visible=visible)
    path = tmp_path / "tabs.uipro"
    commit_project(path, model, expected_token=None)
    assert load_project(path).model == model
    document = DocumentSession(model, registry)
    canvas = DesignerCanvas(document)
    exported = load_export(export_project(model, registry, tmp_path / "export"), qt_app)
    try:
        canvas.resize(1000, 800)
        canvas.show()
        exported.show()
        qt_app.processEvents()
        native = canvas.renderer.tree.widgets[tab]
        runtime = exported.controls[model.nodes[tab].code_name]
        assert native.tab_bar.isHidden() is (not visible)
        assert runtime.tab_bar.isHidden() is (not visible)
        expected = {
            "top": (1, 30, 418, 269), "bottom": (1, 1, 418, 269),
            "left": (30, 1, 389, 298), "right": (1, 1, 389, 298),
        }[position] if visible else (1, 1, 418, 298)
        assert native.pages[0].geometry().getRect() == expected
        assert runtime.pages[0].geometry().getRect() == expected
        assert content_size(model, first) == expected[2:]
        for key in (first, child):
            assert canvas.renderer.tree.widgets[key].mapTo(canvas.renderer.tree.root, QPoint()) == QPoint(*absolute_position(model, key))
        if visible:
            local = native.tab_bar.mapTo(native, native.tab_bar.tabRect(1).center())
            point = canvas.mapFromScene(canvas.renderer.items[tab].mapToScene(QPointF(local)))
            QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
            assert document.model.nodes[tab].properties["current_index"] == 1
        else:
            document.execute("切换隐藏表头页面", lambda m: set_property(m, registry, tab, "current_index", 1))
            assert not canvas.renderer.items[first].isVisible() and canvas.renderer.items[second].isVisible()
        target = canvas.renderer.items[second].mapToScene(QPointF(24, 48))
        added = canvas.create_component("builtin.label", target)
        assert document.model.nodes[added].parent_id == second
        assert document.model.nodes[added].geometry.x >= 0
    finally:
        exported.close()
        exported.deleteLater()
        canvas.dispose()
        canvas.close()
        document.close()


@pytest.mark.parametrize("position", ["top", "bottom", "left", "right"])
def test_auto_hide_and_border_undo(project, registry, qt_app, position):
    model, tab, first, second, child = tab_model(project, registry, tab_position=position,
                                                tab_bar_auto_hide=True, tab_bar_size=48, pane_border=False)
    document = DocumentSession(model, registry)
    canvas = DesignerCanvas(document)
    try:
        native = canvas.renderer.tree.widgets[tab]
        assert not native.tab_bar.isHidden()
        document.execute("删除第二页", lambda m: delete_node(m, second))
        assert native.tab_bar.isHidden()
        assert native.pages[0].geometry() == native.rect()
        assert canvas.renderer.items[child].scenePos() == QPointF(*absolute_position(document.model, child))
        document.undo()
        assert not native.tab_bar.isHidden() and len(native.pages) == 2
        assert native.tab_bar.height() == 48 if position in {"top", "bottom"} else native.tab_bar.width() == 48
        document.execute("手动隐藏", lambda m: set_property(m, registry, tab, "header_visible", False))
        assert native.pages[0].geometry() == native.rect()
        document.undo()
        assert not native.tab_bar.isHidden()
    finally:
        canvas.dispose()
        canvas.close()
        document.close()


def test_tab_icons_move_close(project, registry, qt_app, tmp_path):
    model, tab, first, second, child = tab_model(project, registry, tab_shape="triangular", tab_position="left",
        movable=True, tabs_closable=True, expanding=True, document_mode=True, uses_scroll_buttons=False,
        elide_mode="middle", draw_base=False, icon_width=24, icon_height=20)
    model = set_property(model, registry, first, "tab_icon", image_value(tmp_path))
    model = set_property(model, registry, first, "tool_tip", "第一页的提示")
    verify_registry(registry)
    runtime = load_export(export_project(model, registry, tmp_path / "e"), qt_app)
    try:
        runtime.show()
        qt_app.processEvents()
        tabs = runtime.controls[model.nodes[tab].code_name]
        bar = tabs.tab_bar
        assert bar.shape() == QTabBar.Shape.TriangularWest
        assert bar.isMovable() and bar.tabsClosable() and bar.expanding() and bar.documentMode()
        assert not bar.usesScrollButtons() and not bar.drawBase()
        assert bar.elideMode() == Qt.TextElideMode.ElideMiddle and bar.iconSize() == QSize(24, 20)
        assert not bar.tabIcon(0).isNull() and bar.tabToolTip(0) == "第一页的提示"
        original = list(tabs.pages)
        moved, closed = QSignalSpy(tabs.tabMoved), QSignalSpy(tabs.tabCloseRequested)
        bar.moveTab(0, 1)
        assert tabs.pages == list(reversed(original)) and moved.count() == 1
        tabs.set_current_page(1)
        assert original[0].isVisible() and original[1].isHidden()
        close = bar.tabButton(1, QTabBar.ButtonPosition.RightSide) or bar.tabButton(1, QTabBar.ButtonPosition.LeftSide)
        QTest.mouseClick(close, Qt.MouseButton.LeftButton)
        assert closed.count() == 1 and closed.at(0) == [1]
        assert len(tabs.pages) == 2 and runtime.controls[model.nodes[child].code_name].parentWidget() is original[0]
    finally:
        runtime.close()
        runtime.deleteLater()


@pytest.mark.parametrize("position", ["top", "bottom", "left", "right"])
@pytest.mark.parametrize("visible", [True, False])
def test_scaling_matches_model_and_export(project, registry, qt_app, tmp_path, position, visible):
    model, tab, first, second, child = tab_model(project, registry, tab_position=position,
                                                header_visible=visible, tab_bar_size=44)
    model = set_property(model, registry, model.root_id, "scale_children", True)
    scaled = set_property(model, registry, model.root_id, "geometry.width", 1200)
    scaled = set_property(scaled, registry, scaled.root_id, "geometry.height", 840)
    tree = RuntimeTree(registry)
    runtime = load_export(export_project(model, registry, tmp_path / "scaled-export"), qt_app)
    try:
        tree.apply(compile_plan(scaled, registry, "scaled"))
        runtime.show()
        runtime.resize(1200, 840)
        qt_app.processEvents()
        for key in (first, child):
            exported = runtime.controls[model.nodes[key].code_name]
            assert exported.geometry() == tree.widgets[key].geometry()
            assert exported.mapTo(runtime, QPoint()) == QPoint(*absolute_position(scaled, key))
    finally:
        tree.dispose()
        runtime.close()
        runtime.deleteLater()


def test_old_project_defaults_and_property_panel(project, registry, qt_app, tmp_path):
    model, tab, first, second, child = tab_model(project, registry)
    keep = {"current_index", "background_color", "foreground_color", "font_family", "font_size", "enabled", "visible"}
    old = model.with_nodes({tab: replace(model.nodes[tab], properties=model.nodes[tab].properties.__class__(
        {key: value for key, value in model.nodes[tab].properties.items() if key in keep}))})
    path = tmp_path / "old.uipro"
    commit_project(path, old, expected_token=None)
    loaded = load_project(path).model
    document = DocumentSession(loaded, registry)
    panel = PropertyPanel()
    panel.bind(document)
    try:
        document.select(tab)
        qt_app.processEvents()
        assert panel.editors["header_visible"].isChecked()
        assert panel.editors["tab_position"].currentData() == "top"
        panel.editors["header_visible"].click()
        assert document.model.nodes[tab].properties["header_visible"] is False
        document.undo()
        assert document.model == loaded
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()
        document.close()
