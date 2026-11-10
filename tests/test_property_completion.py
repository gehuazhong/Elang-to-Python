"""新增复合属性的真实行为、数据完整性、撤销和导出检查。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QBuffer, QCoreApplication, QEvent, QIODevice, QPoint, QSize, Qt
from PySide6.QtGui import QColor, QImage, QKeySequence
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QFileDialog, QFontDialog, QFormLayout, QHeaderView, QInputDialog, QListView, QSizePolicy

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.commands.tree_clipboard import copy_tree, paste_tree
from core.document import DocumentSession
from core.errors import DesignerError
from core.storage import commit_project, load_project
from designer.canvas import DesignerCanvas
from panels.properties import PropertyPanel
from runtime.builder import RuntimeTree, verify_registry
from tests.test_codegen import load_export
from widgets.builtin import create_registry


def model_for(project, registry, kind, **values):
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    for name, value in values.items():
        project = set_property(project, registry, key, name, value)
    return project, key


def apply(tree, model, registry):
    tree.apply(compile_plan(model, registry, "属性补全验证"))
    return tree


@pytest.mark.parametrize("kind", ["button", "line_edit", "picture_box", "table_view", "scroll_area", "tab_widget"])
def test_shared_options_undo_and_export(project, registry, qt_app, tmp_path, kind):
    model, key = model_for(project, registry, kind)
    tree = apply(RuntimeTree(registry), model, registry)
    original = tree.widgets[key]
    defaults = (original.cursor().shape(), original.focusPolicy(), original.styleSheet(), original.sizePolicy())
    custom = model
    for name, value in {"cursor_shape": "pointing_hand", "focus_policy": "none", "accessible_name": "示例操作",
                        "style_sheet": "border: 2px solid #246b92;", "size_policy_horizontal": "expanding"}.items():
        custom = set_property(custom, registry, key, name, value)
    commit_project(tmp_path / "source.uipro", custom, expected_token=None)
    assert load_project(tmp_path / "source.uipro").model == custom
    exported = load_export(export_project(custom, registry, tmp_path / "e"), qt_app)
    try:
        apply(tree, custom, registry)
        for widget in (tree.widgets[key], exported.controls[custom.nodes[key].code_name]):
            assert widget.cursor().shape() == Qt.CursorShape.PointingHandCursor
            assert widget.focusPolicy() == Qt.FocusPolicy.NoFocus
            assert widget.accessibleName() == "示例操作"
            assert widget.styleSheet() == "border: 2px solid #246b92;"
            assert widget.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
        apply(tree, model, registry)
        widget = tree.widgets[key]
        assert (widget.cursor().shape(), widget.focusPolicy(), widget.styleSheet(), widget.sizePolicy()) == defaults
        clone, ids = paste_tree(custom, registry, copy_tree(custom, registry, (key,)))
        assert clone.nodes[ids[0]].properties == custom.nodes[key].properties
    finally:
        tree.dispose()
        exported.close()
        exported.deleteLater()


@pytest.mark.parametrize("kind", ["table_widget", "table_view"])
def test_table_sorting_keeps_rows_and_header_sizes(project, registry, qt_app, kind):
    rows = [["2", "two"], ["1", "one"], ["3", "three"]]
    model, key = model_for(project, registry, kind, table_data={"headers": ["ID", "Name"], "rows": rows,
        "column_widths": [44, 126]}, sorting=True, show_horizontal_header=False,
        show_vertical_header=False, row_height=42, header_movable=True)
    tree = apply(RuntimeTree(registry), model, registry)
    try:
        widget = tree.widgets[key]
        assert widget.horizontalHeader().isHidden() and widget.verticalHeader().isHidden()
        assert [widget.rowHeight(i) for i in range(3)] == [42] * 3
        assert [widget.columnWidth(i) for i in range(2)] == [44, 126]
        assert widget.horizontalHeader().sectionsMovable()
        widget.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        changed = set_property(model, registry, key, "table_data", {"headers": ["ID", "Name"],
                              "rows": list(reversed(rows)), "column_widths": [44, 126]})
        apply(tree, changed, registry)
        data = widget.model()
        assert {tuple(data.index(row, col).data() for col in range(2)) for row in range(3)} == {tuple(row) for row in rows}
        changed = set_property(changed, registry, key, "column_resize_mode", "stretch")
        apply(tree, changed, registry)
        assert widget.horizontalHeader().sectionResizeMode(0) == QHeaderView.ResizeMode.Stretch
        apply(tree, model, registry)
        assert [widget.columnWidth(i) for i in range(2)] == [44, 126]
    finally:
        tree.dispose()


def test_super_list_explicit_last_column_is_not_stretched(project, registry, qt_app):
    model, key = model_for(project, registry, "super_list", table_data={"headers": ["A", "B"],
        "rows": [["a", "b"]], "column_widths": [36, 70]}, stretch_last_section=True, header_visible=False)
    tree = apply(RuntimeTree(registry), model, registry)
    try:
        widget = tree.widgets[key]
        assert widget.header().isHidden()
        assert not widget.header().stretchLastSection()
        assert widget.columnWidth(1) == 70
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", ["tree_widget", "tree_view"])
def test_tree_header_collapse_and_restore(project, registry, qt_app, kind):
    model, key = model_for(project, registry, kind, header_text="资源目录", header_hidden=True, expanded=False,
                          tree_data=[{"text": "parent", "children": [{"text": "child", "children": []}]}])
    tree = apply(RuntimeTree(registry), model, registry)
    try:
        widget = tree.widgets[key]
        index = widget.model().index(0, 0)
        assert widget.header().isHidden() and not widget.isExpanded(index)
        assert widget.model().headerData(0, Qt.Orientation.Horizontal) == "资源目录"
        changed = set_property(model, registry, key, "expanded", True)
        changed = set_property(changed, registry, key, "header_hidden", False)
        apply(tree, changed, registry)
        assert not widget.header().isHidden() and widget.isExpanded(widget.model().index(0, 0))
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", ["list_widget", "list_view"])
def test_list_grid_independent_dimensions(project, registry, qt_app, kind):
    model, key = model_for(project, registry, kind, view_mode="icons", grid_width=96, list_wrapping="yes")
    tree = apply(RuntimeTree(registry), model, registry)
    try:
        widget = tree.widgets[key]
        assert widget.viewMode() == QListView.ViewMode.IconMode and widget.isWrapping()
        assert widget.gridSize().width() == 96 and widget.gridSize().height() > 0
        changed = set_property(model, registry, key, "grid_height", 48)
        apply(tree, changed, registry)
        assert widget.gridSize() == QSize(96, 48)
        changed = set_property(changed, registry, key, "view_mode", "list")
        changed = set_property(changed, registry, key, "list_wrapping", "default")
        apply(tree, changed, registry)
        assert not widget.isWrapping() and widget.flow() == QListView.Flow.TopToBottom
    finally:
        tree.dispose()


def test_input_mask_undo_restores_text(project, registry, qt_app):
    model, key = model_for(project, registry, "line_edit", text="123456")
    changed = set_property(model, registry, key, "input_mask", "000-000;_")
    tree = apply(RuntimeTree(registry), changed, registry)
    try:
        assert tree.widgets[key].text() == "123-456"
        assert changed.nodes[key].properties["text"] == "123456"
        apply(tree, model, registry)
        assert tree.widgets[key].text() == "123456" and not tree.widgets[key].inputMask()
    finally:
        tree.dispose()


def test_form_wrap_and_property_panel(project, registry, qt_app):
    model, key = model_for(project, registry, "form_layout", row_wrap_policy="all_rows", horizontal_spacing=20,
                          vertical_spacing=14, field_growth_policy="expanding", layout_alignment="top_left")
    model, label = create_node(model, registry, "builtin.label", 0, 0, parent_id=key)
    model, field = create_node(model, registry, "builtin.line_edit", 0, 0, parent_id=key)
    document = DocumentSession(model, registry)
    canvas, panel = DesignerCanvas(document), PropertyPanel()
    panel.bind(document)
    try:
        document.select(key)
        qt_app.processEvents()
        assert "layout_alignment" in panel.editors and "row_wrap_policy" in panel.editors
        widgets = canvas.renderer.tree.widgets
        assert widgets[field].y() > widgets[label].y()
        assert widgets[key].native_layout.verticalSpacing() == 14
        assert widgets[key].native_layout.fieldGrowthPolicy() == QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()
        canvas.dispose()
        canvas.close()
        canvas.deleteLater()
        document.close()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qt_app.processEvents()


def test_key_sequence_limits_and_export(project, registry, qt_app, tmp_path):
    model, key = model_for(project, registry, "key_sequence_edit", maximum_sequence_length=2,
                          key_sequence="Ctrl+K, Ctrl+C")
    window = load_export(export_project(model, registry, tmp_path / "e"), qt_app)
    try:
        widget = window.controls[model.nodes[key].code_name]
        assert widget.maximumSequenceLength() == 2
        assert widget.keySequence().toString(QKeySequence.SequenceFormat.PortableText) == "Ctrl+K, Ctrl+C"
        document = DocumentSession(model, registry)
        with pytest.raises(DesignerError, match="序列"):
            document.execute("缩短序列", lambda current: set_property(current, registry, key, "maximum_sequence_length", 1))
        assert document.model == model
        document.close()
    finally:
        window.close()
        window.deleteLater()


def test_picture_alignment_opacity_and_border(project, registry, qt_app):
    picture = QImage(20, 20, QImage.Format.Format_ARGB32)
    picture.fill(QColor("#0000ff"))
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert picture.save(buffer, "PNG")
    model, key = model_for(project, registry, "picture_box", image=bytes(buffer.data().toBase64()).decode("ascii"),
                          image_mode="center", image_alignment="top_left", image_opacity=0.5,
                          border=False, background_color="#ffffff")
    tree = apply(RuntimeTree(registry), model, registry)
    try:
        rendered = tree.image(key, 1)
        assert rendered.pixelColor(5, 5).blue() == 255
        assert abs(rendered.pixelColor(5, 5).red() - 128) <= 1
        assert rendered.pixelColor(100, 60) == QColor("#ffffff")
    finally:
        tree.dispose()


def test_raw_tab_bar_auto_hide_restores(project, registry, qt_app, tmp_path):
    model, key = model_for(project, registry, "tab_bar", items=["Only"], auto_hide=True)
    tree = apply(RuntimeTree(registry), model, registry)
    exported = load_export(export_project(model, registry, tmp_path / "e"), qt_app)
    try:
        assert tree.widgets[key].isHidden()
        assert tree.image(key, 1).pixelColor(10, 10).alpha() == 0
        assert exported.controls[model.nodes[key].code_name].isHidden()
        changed = set_property(model, registry, key, "items", ["One", "Two"])
        apply(tree, changed, registry)
        assert not tree.widgets[key].isHidden()
    finally:
        tree.dispose()
        exported.close()
        exported.deleteLater()


@pytest.mark.parametrize("mode", ["multiline", "choices", "integer"])
def test_input_dialog_options_return_values(project, registry, qt_app, mode):
    options = {"multiline": {"multiline": True, "text_value": "first\nsecond"},
               "choices": {"input_items": ["Red", "Blue"], "text_value": "Blue", "items_editable": True},
               "integer": {"input_mode": "integer", "value": 4, "integer_step": 3}}[mode]
    model, key = model_for(project, registry, "input_dialog", ok_text="采用", cancel_text="返回", **options)
    tree = apply(RuntimeTree(registry, design_mode=False), model, registry)
    try:
        service = tree.widgets[key]
        result = QSignalSpy(service.accepted)
        service.open_dialog()
        assert service.native.okButtonText() == "采用" and service.native.cancelButtonText() == "返回"
        if mode == "integer":
            assert service.native.intStep() == 3
        service.native.accept()
        assert result.count() == 1
        assert result.at(0)[0] == {"multiline": "first\nsecond", "choices": "Blue", "integer": 4}[mode]
    finally:
        tree.dispose()


def test_dialog_details_font_and_file_options(project, registry, qt_app, tmp_path):
    model, message = model_for(project, registry, "message_box", informative_text="补充", detailed_text="详情",
                              default_button="取消", modal=True)
    model, font = model_for(model, registry, "font_dialog", font_filter="monospace", use_native_dialog=False)
    model, file = model_for(model, registry, "common_dialog", read_only=True, confirm_overwrite=False,
                            file_view_mode="list", initial_directory=str(tmp_path), initial_file="example.txt")
    tree = apply(RuntimeTree(registry, design_mode=False), model, registry)
    try:
        service = tree.widgets[message]
        service.open_dialog()
        assert service.native.informativeText() == "补充" and service.native.detailedText() == "详情"
        assert service.native.defaultButton().text() == "取消" and service.native.isModal()
        service.native.reject()
        service = tree.widgets[font]
        service.open_dialog()
        assert service.native.testOption(QFontDialog.FontDialogOption.MonospacedFonts)
        service.native.reject()
        service = tree.widgets[file]
        service.open_dialog()
        assert service.dialog.testOption(QFileDialog.Option.ReadOnly)
        assert service.dialog.testOption(QFileDialog.Option.DontConfirmOverwrite)
        assert service.dialog.viewMode() == QFileDialog.ViewMode.List
        service.dialog.reject()
        assert not (tmp_path / "example.txt").exists()
    finally:
        tree.dispose()


def test_lcd_overflow_is_rejected_before_runtime(project, registry):
    model, key = model_for(project, registry, "lcd_number", value=255, digit_count=3)
    document = DocumentSession(model, registry)
    with pytest.raises(DesignerError, match="位数"):
        document.execute("二进制", lambda current: set_property(current, registry, key, "number_mode", "binary"))
    assert document.model == model and document.history.cursor == 0
    document.close()


def test_registry_and_legacy_projects(registry, qt_app):
    verify_registry(registry)
    baseline = create_registry(complete=False)
    assert set(baseline.specs) == set(registry.specs)
    for path in (Path("examples/中文界面示例.uipro"), Path("uidemo/07_兔子工具个人中心/兔子工具个人中心.uipro")):
        model = load_project(path).model
        snapshot = model.to_bytes()
        tree = apply(RuntimeTree(registry), model, registry)
        try:
            assert model.to_bytes() == snapshot
        finally:
            tree.dispose()


def test_svg_animation_stays_disabled_after_reshow(project, registry, qt_app, tmp_path):
    model, key = model_for(project, registry, "svg_widget", animation_enabled=False, keep_aspect_ratio=True)
    tree = apply(RuntimeTree(registry, design_mode=False), model, registry)
    exported = load_export(export_project(model, registry, tmp_path / "e"), qt_app)
    try:
        for window, widget in ((tree.root, tree.widgets[key]), (exported, exported.controls[model.nodes[key].code_name])):
            window.show()
            qt_app.processEvents()
            for _ in range(2):
                assert not widget.native.renderer().isAnimationEnabled()
                assert widget.native.renderer().aspectRatioMode() == Qt.AspectRatioMode.KeepAspectRatio
                widget.hide()
                widget.show()
                qt_app.processEvents()
            assert not widget.native.renderer().isAnimationEnabled()
    finally:
        tree.dispose()
        exported.close()
        exported.deleteLater()
