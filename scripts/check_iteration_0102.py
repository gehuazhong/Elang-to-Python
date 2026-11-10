"""Exercise common dialogs, tab refreshes and failed exports on real Qt backends."""

import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QColorDialog, QDialog, QFileDialog, QMainWindow
from shiboken6 import isValid


def flush_deletes():
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def check_window(window, controls, directory):
    window.show()
    QApplication.processEvents()
    service, tabs, timer = (controls[key] for key in ("dialog", "tabs", "timer"))
    source = directory / "selection.txt"
    source.write_text("file selection must not change this", encoding="utf-8")
    results = {}
    for kind in ("color", "font", "open_file", "open_files", "save_file", "directory"):
        service.values.update(dialog_kind=kind, use_native_dialog=False, confirm_overwrite=False)
        accepted, cancelled = QSignalSpy(service.accepted), QSignalSpy(service.cancelled)

        def reopen(*args):
            service.open_dialog()

        service.accepted.connect(reopen)
        service.cancelled.connect(reopen)
        try:
            service.open_dialog()
            for index in range(12):
                first = service.dialog
                if isinstance(first, QColorDialog):
                    first.setCurrentColor(QColor("#234567"))
                elif isinstance(first, QFileDialog):
                    first.selectFile(str(directory if kind == "directory" else source))
                first.reject() if index % 2 else first.accept()
                current = service.dialog
                assert current is not first and current.isVisible()
                first.finished.emit(QDialog.DialogCode.Rejected)
                assert service.dialog is current
                flush_deletes()
                assert not isValid(first) and isValid(current)
                assert window.findChildren(QDialog) == [current]
            assert accepted.count() == cancelled.count() == 6
            if kind == "color":
                assert accepted.at(0) == ["#234567"]
            elif kind == "font":
                assert set(accepted.at(0)[0]) == {"字体", "字号", "粗体", "斜体"}
            else:
                assert [Path(value) for value in accepted.at(0)[0]] == [directory if kind == "directory" else source]
            results[kind] = {"accepted": accepted.count(), "cancelled": cancelled.count(), "reopens": 12}
        finally:
            service.accepted.disconnect(reopen)
            service.cancelled.disconnect(reopen)
            service.dispose()
            flush_deletes()

    values = {"items": ["first", "second", "third"], "current_index": 0,
              "tabs_closable": False, "movable": True, "expanding": False}
    tabs.configure(values)
    tabs.setTabData(2, {"record": 42})
    tabs.setCurrentIndex(2)
    tabs.moveTab(2, 0)
    changes = QSignalSpy(tabs.currentChanged)
    for index in range(50):
        tabs.configure({**values, "expanding": bool(index % 2)})
    assert tabs.tabText(tabs.currentIndex()) == "third"
    assert tabs.tabData(tabs.currentIndex()) == {"record": 42} and changes.count() == 0

    service.values["dialog_kind"] = "color"
    service.open_dialog()
    original = service.dialog
    assert timer.isActive()
    assert window.close()
    QApplication.processEvents()
    flush_deletes()
    assert service.dialog is None and not isValid(original) and not timer.isActive()
    assert source.read_text(encoding="utf-8") == "file selection must not change this"
    return {"platform": QApplication.platformName(), "dialogs": results,
            "tab_refreshes_without_data_loss": 50, "close_releases_dialog_and_timer": True}


def check_failed_export(entry, application):
    launcher = runpy.run_path(str(entry), run_name="iteration_export_probe")
    handlers = sorted((entry.parent / "event_handlers").glob("on_*.py"))
    assert len(handlers) == 1
    handler = handlers[0]
    content = handler.read_bytes()
    before = {window for window in QApplication.topLevelWidgets() if isinstance(window, QMainWindow)}
    modules = {name for name in sys.modules if name.startswith("_uiplay_event_")}
    try:
        handler.write_text("def broken(:\n", encoding="utf-8")
        try:
            launcher["create_window"](application)
        except SyntaxError:
            pass
        else:
            raise AssertionError("Broken handler unexpectedly loaded")
        flush_deletes()
        assert {window for window in QApplication.topLevelWidgets() if isinstance(window, QMainWindow)} == before
        assert {name for name in sys.modules if name.startswith("_uiplay_event_")} == modules
    finally:
        handler.write_bytes(content)
    return launcher["create_window"](application)


def main():
    application = QApplication([])
    application.setQuitOnLastWindowClosed(False)
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        entry = Path(sys.argv[2])
        names = json.loads(sys.argv[3])
        window = check_failed_export(entry, application)
        try:
            result = check_window(window, {key: window.controls[name] for key, name in names.items()}, entry.parent)
        finally:
            window.deleteLater()
            flush_deletes()
        assert not any(name.split(".")[0] in {"core", "designer", "panels"} for name in sys.modules)
        result.update(failed_startup_cleanup=True, retry_after_repair=True, isolated=True)
        print(json.dumps(result))
        return

    from app.version import VERSION
    from codegen.publisher import export_project
    from core.build_plan import compile_plan
    from core.commands.nodes import create_node, set_property
    from core.events import set_event_enabled
    from core.models import new_project
    from core.storage import commit_project, load_project
    from runtime.advanced_widgets import start_advanced
    from runtime.application import configure_application
    from runtime.builder import RuntimeTree
    from runtime.easy_widgets import start_components
    from scripts.source_fingerprint import source_fingerprint
    from widgets.builtin import create_registry

    configure_application(application)
    base = Path(__file__).resolve().parents[1]
    output = base / "reports/iteration-0102"
    output.mkdir(parents=True, exist_ok=True)
    registry = create_registry()
    model = new_project("0.10.2 runtime verification")
    names = {}
    for index, (alias, kind) in enumerate((("dialog", "common_dialog"), ("tabs", "tab_bar"),
                                          ("timer", "timer"), ("button", "button"), ("table", "table_widget"))):
        model, key = create_node(model, registry, "builtin." + kind, 20, 20 + index * 45)
        names[alias] = model.nodes[key].code_name
        if kind == "button":
            model = set_event_enabled(model, registry, key, "clicked", True)
        elif kind == "table_widget":
            model = set_property(model, registry, key, "table_data", {
                "rows": [["two", "2"], ["one", "1"]], "headers": ["name", "id"], "column_widths": [150, 80]})
        elif kind == "timer":
            model = set_property(model, registry, key, "auto_start", True)
    with tempfile.TemporaryDirectory(prefix="uiplay_0102_") as temporary:
        directory = Path(temporary)
        entry = export_project(model, registry, directory / "export")
        first = (entry.parent / "current.json").read_bytes()
        project = directory / "roundtrip.uipro"
        commit_project(project, model, expected_token=None)
        restored = load_project(project).model
        export_project(restored, registry, entry.parent)
        assert (entry.parent / "current.json").read_bytes() == first
        assert len(list((entry.parent / "generated").iterdir())) == 1

        tree = RuntimeTree(registry, design_mode=False)
        try:
            tree.apply(compile_plan(restored, registry, "native lifecycle check"))
            controls = {node.code_name: tree.widgets[key] for key, node in model.nodes.items()}
            start_components(controls)
            start_advanced(controls)
            native = check_window(tree.root, {key: controls[name] for key, name in names.items()}, directory)
        finally:
            tree.dispose()
            flush_deletes()

        process = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--export", str(entry), json.dumps(names)],
                                 cwd=entry.parent, env={**os.environ, "QT_QPA_PLATFORM": application.platformName()},
                                 capture_output=True, text=True, encoding="utf-8", timeout=120)
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        exported = json.loads(process.stdout.strip().splitlines()[-1])
        result = {"version": VERSION, "native": native, "isolated_export": exported,
                  "save_reload_keeps_export_version": True, "registry_fingerprint": registry.fingerprint,
                  "source_fingerprint": source_fingerprint(base)}
        (output / "runtime.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))


if __name__ == "__main__":
    main()
