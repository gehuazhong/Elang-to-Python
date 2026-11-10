"""Saving a project must not churn exports; failed startup must release Qt objects."""

import sys

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QMainWindow
from shiboken6 import delete, isValid

from codegen.generator import generate_files
from codegen.publisher import export_project
from core.commands.nodes import create_node, set_property
from core.events import event_bindings, set_event_enabled
from core.storage import commit_project, load_project
from tests.test_codegen import load_export


@pytest.mark.parametrize("kind", ["table_widget", "super_list", "table_view"])
def test_save_reload_keeps_generated_bytes_and_version(project, registry, tmp_path, kind):
    model, key = create_node(project, registry, "builtin." + kind, 20, 20)
    model = set_property(model, registry, key, "table_data", {
        "headers": ["编号", "说明"], "rows": [["02", "引号 ' 与 \\ 路径"], ["01", "保留行顺序"]],
        "column_widths": [84, 210]})
    before = generate_files(model, registry)
    target = tmp_path / "export"
    export_project(model, registry, target)
    first_pointer = (target / "current.json").read_bytes()
    source = tmp_path / "saved.uipro"
    commit_project(source, model, expected_token=None)
    restored = load_project(source).model
    assert restored == model
    assert generate_files(restored, registry) == before
    export_project(restored, registry, target)
    assert (target / "current.json").read_bytes() == first_pointer
    assert len(list((target / "generated").iterdir())) == 1
    window_files = generate_files(set_property(restored, registry, key, "table_data", {
        "rows": [["01", "保留行顺序"], ["02", "引号 ' 与 \\ 路径"]],
        "column_widths": [84, 210], "headers": ["编号", "说明"]}), registry)
    assert window_files["ui_main.py"] != before["ui_main.py"], "Row order is meaningful"


@pytest.mark.parametrize("failure", ["missing", "syntax", "wrong_function"])
def test_failed_event_initialization_releases_window(project, registry, qt_app, tmp_path, failure):
    model, key = create_node(project, registry, "builtin.button", 20, 20)
    model = set_event_enabled(model, registry, key, "clicked", True)
    model, second = create_node(model, registry, "builtin.button", 20, 80)
    model = set_event_enabled(model, registry, second, "clicked", True)
    entry = export_project(model, registry, tmp_path)
    handler = event_bindings(model, registry)[1]["handler"]
    source = tmp_path / "event_handlers" / (handler + ".py")
    if failure == "missing":
        source.unlink()
    elif failure == "syntax":
        source.write_text("def broken(:\n", encoding="utf-8")
    else:
        source.write_text("def different(window):\n    return None\n", encoding="utf-8")
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    before = {w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow)}
    modules = {name for name in sys.modules if name.startswith("_uiplay_event_")}
    try:
        with pytest.raises((FileNotFoundError, SyntaxError, RuntimeError)):
            load_export(entry, qt_app)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        remaining = {w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow)}
        assert remaining == before, "Failed UI construction retained a top-level window"
        assert {name for name in sys.modules if name.startswith("_uiplay_event_")} == modules
    finally:
        for window in set(QApplication.topLevelWidgets()) - before:
            if isinstance(window, QMainWindow) and isValid(window):
                delete(window)


def test_export_retry_after_event_repair(project, registry, qt_app, tmp_path):
    model, key = create_node(project, registry, "builtin.button", 20, 20)
    model = set_event_enabled(model, registry, key, "clicked", True)
    entry = export_project(model, registry, tmp_path)
    handler = event_bindings(model, registry)[0]["handler"]
    source = tmp_path / "event_handlers" / (handler + ".py")
    source.write_text("raise RuntimeError('broken import')\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="broken import"):
        load_export(entry, qt_app)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    source.write_text(f"def {handler}(window, *args):\n    window.setWindowTitle('repaired')\n", encoding="utf-8")
    window = load_export(entry, qt_app)
    try:
        window.controls[model.nodes[key].code_name].click()
        assert window.windowTitle() == "repaired"
    finally:
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
