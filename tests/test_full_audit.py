"""跨功能审计：配置恢复、模型刷新和资源释放。"""

from dataclasses import replace

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QItemSelectionModel, QSettings, Qt

from app.main_window import MainWindow
from app.workbench_settings import apply_preferences, current_preferences, save_workbench
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from runtime.builder import RuntimeTree


def drain(app):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


@pytest.mark.parametrize("kind", ["list_view", "table_view", "tree_view", "column_view"])
def test_model_style_update_preserves_model_and_selection(project, registry, qt_app, kind):
    project, key = create_node(project, registry, "builtin." + kind, 10, 10)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        model, selection = widget.model(), widget.selectionModel()
        selection.setCurrentIndex(model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        current = selection.currentIndex()
        changed = set_property(project, registry, key, "foreground_color", "#246b92")
        tree.apply(compile_plan(changed, registry, "style"))
        assert widget.model() is model
        assert widget.selectionModel() is selection
        assert selection.currentIndex() == current
    finally:
        tree.dispose()
        drain(qt_app)


@pytest.mark.parametrize("kind", ["list_view", "table_view", "tree_view", "column_view"])
def test_replacing_view_content_does_not_accumulate_selection_models(project, registry, qt_app, kind):
    project, key = create_node(project, registry, "builtin." + kind, 10, 10)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        count = lambda: len(widget.findChildren(QItemSelectionModel, options=Qt.FindChildOption.FindDirectChildrenOnly))
        baseline = count()
        for index in range(12):
            if kind == "list_view":
                name, value = "items", [f"row {index}"]
            elif kind == "table_view":
                name, value = "table_data", {"headers": ["Name"], "rows": [[f"row {index}"]]}
            else:
                name, value = "tree_data", [{"text": f"row {index}", "children": []}]
            changed = set_property(project, registry, key, name, value)
            tree.apply(compile_plan(changed, registry, "content"))
            drain(qt_app)
        assert count() == baseline
        assert widget.model().index(0, 0).data() == "row 11"
    finally:
        tree.dispose()
        drain(qt_app)


@pytest.mark.parametrize("value", ["corrupt-layout", 123, [1, 2]])
def test_invalid_native_window_settings_do_not_prevent_startup(qt_app, registry, tmp_path, value):
    settings = QSettings(str(tmp_path / "bad.ini"), QSettings.Format.IniFormat)
    settings.setValue("window/geometry", value)
    settings.setValue("window/state_v2", value)
    window = MainWindow(registry, settings=settings, enable_recovery=False)
    try:
        assert window.document is not None
        assert not window.geometry_restored and not window.layout_restored
    finally:
        window.discard_all_for_test()
        window.close()
        window.deleteLater()
        drain(qt_app)


def test_custom_property_column_width_survives_restart(qt_app, registry, tmp_path):
    settings = QSettings(str(tmp_path / "columns.ini"), QSettings.Format.IniFormat)
    first = MainWindow(registry, settings=settings, enable_recovery=False)
    try:
        apply_preferences(first, replace(current_preferences(first), font_size=12))
        first.properties.tree.setColumnWidth(0, 177)
        assert save_workbench(first)
        second = MainWindow(registry, settings=settings, enable_recovery=False)
        try:
            assert second.properties.tree.columnWidth(0) == 177
            assert second.properties.search.font().pointSize() == 12
        finally:
            second.discard_all_for_test()
            second.close()
            second.deleteLater()
    finally:
        first.discard_all_for_test()
        first.close()
        first.deleteLater()
        drain(qt_app)
