"""Navigation survives editing, page changes, native clicks and export."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QGraphicsScene

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.arrange import stack_nodes
from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.group_clipboard import copy_group, paste_group
from core.commands.nodes import create_node, delete_node, set_property
from core.commands.tree_clipboard import copy_tree, decode_tree, encode_tree, paste_tree
from core.document import DocumentSession
from core.errors import DesignerError
from core.hierarchy import pages
from core.models import new_project
from core.storage import commit_project, load_project
from designer.renderer import CanvasRenderer
from panels.properties import PropertyPanel
from runtime.builder import RuntimeTree
from runtime.navigation import ACTIVE_PROPERTY, PageNavigation
from runtime.preview import PreviewRuntime
from tests.test_codegen import load_export
from tests.test_storage import wait_for


def navigation_model(model, registry, container_kind="tab_widget", button_kind="button"):
    model, container = create_node(model, registry, "builtin." + container_kind, 200, 20)
    first, second = pages(model, container)
    buttons = []
    for index, page in enumerate((first, second)):
        model, key = create_node(model, registry, "builtin." + button_kind, 16, 40 + index * 56)
        for prop, value in (("navigation_page", page.code_name), ("navigation_style", "sidebar")):
            model = set_property(model, registry, key, prop, value)
        buttons.append(key)
    return model, container, (first.id, second.id), tuple(buttons)


def current(container):
    return container.tab_bar.currentIndex() if hasattr(container, "tab_bar") else container.currentIndex()


def select(container, index):
    container.set_current_page(index) if hasattr(container, "tab_bar") else container.setCurrentIndex(index)


@pytest.mark.parametrize("container_kind", ["tab_widget", "stacked_widget", "tool_box"])
@pytest.mark.parametrize("button_kind", ["button", "tool_button", "command_link_button"])
def test_runtime_and_export_navigation(project, registry, qt_app, tmp_path, container_kind, button_kind):
    model, container, page_ids, buttons = navigation_model(project, registry, container_kind, button_kind)
    before = model.to_bytes()
    tree = RuntimeTree(registry, design_mode=False)
    exported = None
    try:
        plan = compile_plan(model, registry, "navigation")
        tree.apply(plan)
        tree.apply(plan)
        tree.apply(plan)
        exported = load_export(export_project(model, registry, tmp_path / "export"), qt_app)
        for root, controls in ((tree.root, tree.widgets),
                               (exported, {key: exported.controls[node.code_name] for key, node in model.nodes.items()})):
            root.show()
            qt_app.processEvents()
            nav = [controls[key] for key in buttons]
            target = controls[container]
            assert [button.property(ACTIVE_PROPERTY) for button in nav] == [True, False]
            spy = QSignalSpy(target.currentChanged)
            QTest.mouseClick(nav[1], Qt.MouseButton.LeftButton)
            assert current(target) == 1 and spy.count() == 1
            assert [button.property(ACTIVE_PROPERTY) for button in nav] == [False, True]
            assert not any(button.isCheckable() for button in nav)
            nav[1].click()
            assert spy.count() == 1
            select(target, 0)
            assert [button.property(ACTIVE_PROPERTY) for button in nav] == [True, False]
            assert sum(type(child).__name__ == "PageNavigation" for child in nav[1].children()) == 1
        assert model.to_bytes() == before
    finally:
        tree.dispose()
        if exported:
            exported.close()
            exported.deleteLater()


def test_moving_live_tabs_keeps_target_identity(project, registry, qt_app):
    model, container, page_ids, buttons = navigation_model(project, registry)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "reorder"))
        target = tree.widgets[container]
        target.tab_bar.moveTab(1, 0)
        tree.widgets[buttons[1]].click()
        assert target.pages[current(target)] is tree.widgets[page_ids[1]]
        assert tree.widgets[buttons[1]].property(ACTIVE_PROPERTY) is True
        assert tree.widgets[buttons[0]].property(ACTIVE_PROPERTY) is False
    finally:
        tree.dispose()


def test_rebind_unbind_delete_and_undo(project, registry, qt_app):
    model, container, page_ids, buttons = navigation_model(project, registry)
    document = DocumentSession(model, registry)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        def apply():
            tree.apply(compile_plan(document.model, registry, "edit"))
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        apply()
        button = tree.widgets[buttons[1]]
        document.execute("rebind", lambda m: set_property(m, registry, buttons[1], "navigation_page", m.nodes[page_ids[0]].code_name))
        apply()
        select(tree.widgets[container], 1)
        button.click()
        assert current(tree.widgets[container]) == 0
        assert len(button.findChildren(PageNavigation)) == 1
        document.execute("unbind", lambda m: set_property(m, registry, buttons[1], "navigation_page", ""))
        apply()
        select(tree.widgets[container], 1)
        button.click()
        assert current(tree.widgets[container]) == 1
        assert button.property(ACTIVE_PROPERTY) is False
        assert not button.findChildren(PageNavigation)
        document.undo()
        document.undo()
        apply()
        document.execute("delete page", lambda m: delete_node(m, page_ids[1]))
        assert document.model.nodes[buttons[1]].properties["navigation_page"] == ""
        apply()
        button.click()
        assert current(tree.widgets[container]) == 0
        document.undo()
        apply()
        button.click()
        assert current(tree.widgets[container]) == 1
        document.execute("delete container", lambda m: delete_node(m, container))
        apply()
        assert all(not tree.widgets[key].findChildren(PageNavigation) for key in buttons)
    finally:
        tree.dispose()
        document.close()


def test_canvas_highlight_and_design_clicks_do_not_change_pages(project, registry, qt_app):
    model, container, page_ids, buttons = navigation_model(project, registry)
    scene = QGraphicsScene()
    renderer = CanvasRenderer(scene, registry)
    try:
        renderer.apply(compile_plan(model, registry, "canvas"), model.data["canvas"], 1)
        before = renderer.items[buttons[1]].pixmap().toImage()
        renderer.tree.widgets[buttons[1]].click()
        assert current(renderer.tree.widgets[container]) == 0
        model = set_property(model, registry, container, "current_index", 1)
        renderer.apply(compile_plan(model, registry, "canvas"), model.data["canvas"], 1)
        assert renderer.tree.widgets[buttons[1]].property(ACTIVE_PROPERTY) is True
        assert renderer.items[buttons[1]].pixmap().toImage() != before
    finally:
        renderer.dispose()


def test_overlay_button_becomes_clickable_in_preview(project, registry, qt_app):
    model, container, page_ids, buttons = navigation_model(project, registry)
    model, label = create_node(model, registry, "builtin.label", 16, 96)
    model = set_property(model, registry, label, "text", "Overlay")
    preview = PreviewRuntime(registry)
    try:
        preview.show(compile_plan(model, registry, "overlay"), model)
        host = preview.tree.root.centralWidget()
        point = QPoint(32, 108)
        assert host.childAt(point) is preview.tree.widgets[label]
        model = stack_nodes(model, (buttons[1],), "front")
        preview.show(compile_plan(model, registry, "front"), model)
        hit = host.childAt(point)
        assert hit is preview.tree.widgets[buttons[1]]
        QTest.mouseClick(hit, Qt.MouseButton.LeftButton, pos=hit.mapFrom(host, point))
        assert current(preview.tree.widgets[container]) == 1
    finally:
        preview.dispose()


def test_clipboard_internal_remap_and_external_reference_omission(project, registry, tmp_path):
    model, container, page_ids, buttons = navigation_model(project, registry)
    single = copy_fragment(model, registry, buttons[0])
    assert single.omitted_connections == 1
    pasted, key = paste_fragment(new_project(), registry, single)
    assert pasted.nodes[key].properties["navigation_page"] == ""
    group = copy_group(model, registry, buttons)
    assert group.omitted_connections == 2
    pasted, keys = paste_group(new_project(), registry, group)
    assert all(pasted.nodes[key].properties["navigation_page"] == "" for key in keys)
    external = copy_tree(model, registry, buttons)
    assert external.omitted_connections == 2
    fragment = decode_tree(encode_tree(copy_tree(model, registry, (container, *buttons))), registry)
    assert fragment.omitted_connections == 0
    for destination in (model, new_project()):
        pasted, roots = paste_tree(destination, registry, fragment, offset=0)
        registry.validate(pasted)
        copied_pages = pages(pasted, roots[0])
        assert [pasted.nodes[key].properties["navigation_page"] for key in roots[1:]] == [p.code_name for p in copied_pages]
        path = tmp_path / (destination.data["document_id"] + ".uipro")
        commit_project(path, pasted, expected_token=None)
        assert load_project(path).model == pasted


def test_inspector_page_choice_and_renaming(project, registry, qt_app):
    model, container, page_ids, buttons = navigation_model(project, registry)
    document = DocumentSession(model, registry)
    panel = PropertyPanel()
    try:
        document.select(buttons[0])
        panel.bind(document)
        panel.refresh()
        editor = panel.editors["navigation_page"]
        assert editor.count() == 3
        assert editor.currentData() == model.nodes[page_ids[0]].code_name
        editor.activated.emit(2)
        assert document.model.nodes[buttons[0]].properties["navigation_page"] == model.nodes[page_ids[1]].code_name
        document.execute("rename page", lambda m: set_property(m, registry, page_ids[1], "text", "Renamed page"))
        panel.refresh()
        assert "Renamed page" in panel.editors["navigation_page"].currentText()
        document.undo()
        document.undo()
        assert document.model == model
        for invalid in ("missing_page", model.nodes[buttons[0]].code_name, model.nodes[container].code_name):
            with pytest.raises(DesignerError, match="关联页面"):
                document.execute("invalid", lambda m: set_property(m, registry, buttons[0], "navigation_page", invalid))
        assert document.model == model
    finally:
        panel.bind(None)
        panel.deleteLater()
        document.close()


def test_style_reset_and_preserved_check_state(project, registry, qt_app):
    model, container, page_ids, buttons = navigation_model(project, registry)
    model = set_property(model, registry, buttons[1], "checked", True)
    model = set_property(model, registry, buttons[1], "style_sheet", "color: rgb(12, 34, 56);")
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "style"))
        button = tree.widgets[buttons[1]]
        assert button.isChecked() and button.property(ACTIVE_PROPERTY) is False
        assert button.palette().buttonText().color().getRgb()[:3] == (12, 34, 56)
        select(tree.widgets[container], 1)
        assert button.isChecked() and button.property(ACTIVE_PROPERTY) is True
        for index in range(3):
            model = set_property(model, registry, buttons[1], "text", str(index))
            tree.apply(compile_plan(model, registry, "style refresh"))
        assert button.styleSheet().count("border-radius: 5px") == 1
        model = set_property(model, registry, buttons[1], "navigation_style", "default")
        tree.apply(compile_plan(model, registry, "style reset"))
        assert button.styleSheet() == "color: rgb(12, 34, 56);"
        button.click()
        assert current(tree.widgets[container]) == 1
    finally:
        tree.dispose()


@pytest.mark.parametrize("container_kind", ["tab_widget", "stacked_widget", "tool_box"])
def test_target_destroyed_externally_disconnects_button(project, registry, qt_app, container_kind):
    model, container, page_ids, buttons = navigation_model(project, registry, container_kind)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "destroyed target"))
        target = tree.widgets[page_ids[1]]
        button = tree.widgets[buttons[1]]
        target.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert button._page_navigation is None
        assert button.property(ACTIVE_PROPERTY) is False
        button.click()
        # The test simulates business code deleting a page outside the model.
        tree.widgets.pop(page_ids[1])
    finally:
        tree.dispose()


def test_shortcut_and_disabled_button_navigation(project, registry, qt_app):
    model, container, page_ids, buttons = navigation_model(project, registry)
    model = set_property(model, registry, buttons[1], "shortcut", "Alt+2")
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "shortcut"))
        tree.root.show()
        tree.root.activateWindow()
        QTest.qWait(30)
        QTest.keyClick(tree.root, Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier)
        wait_for(lambda: current(tree.widgets[container]) == 1, qt_app)
        select(tree.widgets[container], 0)
        tree.widgets[buttons[1]].setEnabled(False)
        QTest.mouseClick(tree.widgets[buttons[1]], Qt.MouseButton.LeftButton)
        assert current(tree.widgets[container]) == 0
    finally:
        tree.dispose()
