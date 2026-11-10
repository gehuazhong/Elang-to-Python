"""Check copied triggers and repeatable dialogs on native, preview and exported paths."""

import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

from PySide6.QtCore import QCoreApplication, QEvent, Qt, QTimer
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QPushButton
from shiboken6 import isValid


def check_window(window, controls):
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
    window.show()
    QApplication.processEvents()
    dialogs = [controls[name] for name in ("dialog_1", "dialog_1_copy")]
    for dialog in dialogs:
        dialog.hide()
    for index, name in enumerate(("button_1", "button_1_copy")):
        controls[name].click()
        assert dialogs[index].isVisible() and not dialogs[1 - index].isVisible()
        dialogs[index].reject()

    service = controls["input_dialog_1"]
    accepted, cancelled = QSignalSpy(service.accepted), QSignalSpy(service.cancelled)
    def reopen(*args):
        service.open_dialog()
    service.accepted.connect(reopen)
    service.cancelled.connect(reopen)
    try:
        service.open_dialog()
        for index in range(12):
            original = service.native
            if index % 2:
                original.reject()
            else:
                original.setTextValue(str(index))
                original.accept()
            assert service.native is not original and service.native.isVisible()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            assert isValid(service.native)
        assert accepted.count() == cancelled.count() == 6
        assert [accepted.at(index)[0] for index in range(6)] == [str(index) for index in range(0, 12, 2)]
    finally:
        service.accepted.disconnect(reopen)
        service.cancelled.disconnect(reopen)
        service.dispose()

    progress = controls["progress_dialog_1"]
    completed, cancelled = QSignalSpy(progress.accepted), QSignalSpy(progress.cancelled)
    for auto_close in (True, False):
        for auto_reset in (True, False):
            progress.configure({**progress.values, "auto_close": auto_close, "auto_reset": auto_reset})
            progress.open_dialog()
            assert progress.native.value() == 0
            progress.setValue(50)
            progress.setValue(100)
            progress.setValue(100)
            if not auto_close:
                assert progress.native.isVisible()
            progress.open_dialog()
            assert progress.native.value() == 0
            progress.native.findChild(QPushButton).click()
            progress.setValue(100)
            assert progress.native is None
    assert completed.count() == cancelled.count() == 4
    progress.configure({**progress.values, "maximum": 0})
    progress.open_dialog()
    progress.setValue(0)
    assert completed.count() == 4
    progress.dispose()
    return {"platform": QApplication.platformName(), "independent_copied_triggers": 2,
            "input_callback_reopens": 12, "progress_option_combinations": 4,
            "completion_and_cancellation_once": True, "busy_progress_not_completed": True}


def fixture(registry):
    from core.commands.group_clipboard import copy_group, paste_group
    from core.commands.nodes import create_node, set_property
    from core.events import set_event_enabled
    from core.models import new_project

    model = new_project("Dialog lifecycle verification")
    model, button = create_node(model, registry, "builtin.button", 16, 16)
    model, dialog = create_node(model, registry, "builtin.dialog", 180, 16)
    model = set_property(model, registry, dialog, "trigger_control", model.nodes[button].code_name)
    model = set_event_enabled(model, registry, dialog, "accepted", True)
    model, _ = paste_group(model, registry, copy_group(model, registry, (button, dialog)))
    for kind in ("input_dialog", "progress_dialog"):
        model, key = create_node(model, registry, "builtin." + kind, 0, 0)
        model = set_event_enabled(model, registry, key, "accepted", True)
        model = set_event_enabled(model, registry, key, "cancelled", True)
    registry.validate(model)
    return model


def check_designer(registry, directory, output):
    from PySide6.QtCore import QMimeData, QPointF, QSettings
    from app.bootstrap import initialize
    from app.main_window import MainWindow

    app = QApplication.instance()
    initialize(app, configure_logging=False)
    clipboard = app.clipboard()
    previous = clipboard.mimeData()
    saved = {key: bytes(previous.data(key)) for key in previous.formats()} if previous else {}
    window = MainWindow(registry, settings=QSettings(str(directory / "designer.ini"), QSettings.Format.IniFormat),
                        enable_recovery=False, persist_settings=False)
    try:
        window.show()
        window.activateWindow()
        QTest.qWait(30)
        canvas, document, view = window.page.canvas, window.document, window.object_tree
        keys = [canvas.create_component("builtin." + kind, QPointF(0, 0)) for kind in ("timer", "input_dialog")]
        app.processEvents()
        view.setFocus()
        for key, modifier in zip(keys, (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ControlModifier)):
            point = view.visualItemRect(view._items[key]).center()
            QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, modifier, point)
        assert set(document.selected_ids) == set(keys)
        before = document.model.to_bytes()
        QTest.keyClick(view, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(view, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()
        assert len(document.model.nodes) == 6 and len(document.selected_ids) == 2
        assert not set(document.selected_ids) & set(keys)
        assert "排版" not in window.properties.validation_message.text()
        assert not window.actions["arrange_same_size"].isEnabled()
        assert window.grab().save(str(output / "nonvisual-selection.png"))
        after = document.model.to_bytes()
        document.undo()
        assert document.model.to_bytes() == before
        document.redo()
        assert document.model.to_bytes() == after
        return {"ctrl_multiselection": True, "copy_paste_shortcuts": True, "atomic_undo_redo": True}
    finally:
        window.discard_all_for_test()
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        if saved:
            restored = QMimeData()
            for key, data in saved.items():
                restored.setData(key, data)
            clipboard.setMimeData(restored)
        else:
            clipboard.clear()


def main():
    app = QApplication([])
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        module = runpy.run_path(sys.argv[2], run_name="iteration_export_check")
        window = module["create_window"](app)
        try:
            result = check_window(window, window.controls)
        finally:
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert not any(name.split(".")[0] in {"core", "designer", "panels"} for name in sys.modules)
        print(json.dumps(result))
        return

    from runtime.application import configure_application
    configure_application(app)
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        from preview.worker import Worker
        output = Path(sys.argv[2])

        class Probe(Worker):
            def send(self, kind, **values):
                super().send(kind, **values)
                if kind == "ready":
                    QTimer.singleShot(0, self.check)

            def check(self):
                try:
                    tree = self.runtime.tree
                    controls = {node.code_name: tree.widgets[key] for key, node in tree.plans.items()}
                    result = check_window(tree.root, controls)
                    output.write_text(json.dumps(result), encoding="utf-8")
                    tree.root.close()
                except Exception as error:
                    self.fail(repr(error))

        raise SystemExit(Probe(app, sys.stdout.buffer).run())

    from codegen.publisher import export_project
    from core.build_plan import compile_plan
    from core.storage import commit_project, load_project
    from preview.service import PreviewService
    from runtime.builder import RuntimeTree
    from scripts.source_fingerprint import source_fingerprint
    from widgets.builtin import create_registry

    base = Path(__file__).resolve().parents[1]
    output = base / "reports/iteration-20261111"
    output.mkdir(parents=True, exist_ok=True)
    registry = create_registry()
    model = fixture(registry)
    compatibility = {}
    for relative in ("uidemo/07_兔子工具个人中心/兔子工具个人中心.uipro",
                     "uidemo/08_万金油UI/万金油UI.uipro", "uidemo/08_万金油UI/万金油UI_导航增强.uipro"):
        source = base / relative
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        original = load_project(source).model
        compile_plan(original, registry, "existing project compatibility")
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        compatibility[relative] = {"nodes": len(original.nodes), "sha256": digest}
    with tempfile.TemporaryDirectory(prefix="uiplay_iteration_") as temporary:
        directory = Path(temporary)
        designer = check_designer(registry, directory, output)
        project = directory / "roundtrip.uipro"
        commit_project(project, model, expected_token=None)
        assert load_project(project).model.to_bytes() == model.to_bytes()
        tree = RuntimeTree(registry, design_mode=False)
        try:
            plan = compile_plan(model, registry, "iteration native check")
            for _ in range(4):
                tree.apply(plan)
            controls = {node.code_name: tree.widgets[node.id] for node in model.nodes.values()}
            native = check_window(tree.root, controls)
        finally:
            tree.dispose()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

        entry = export_project(model, registry, directory / "export")
        process = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--export", str(entry)],
                                 cwd=entry.parent, env={**os.environ, "QT_QPA_PLATFORM": app.platformName()},
                                 capture_output=True, text=True, encoding="utf-8", timeout=60)
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        exported = json.loads(process.stdout.strip().splitlines()[-1])

        preview_output = directory / "preview.json"
        service = PreviewService(registry)
        service._command = lambda: (sys.executable, ["-X", "utf8", "-u", "-m", "scripts.check_iteration_runtime",
                                                   "--preview", str(preview_output)])
        try:
            service.start(model, "iteration-check", "iteration-session")
            for _ in range(1000):
                QTest.qWait(20)
                if not service.active:
                    break
            assert not service.active and service.last_ready and not service.last_error, service.last_error
            assert service.last_ready["process_id"] != os.getpid()
            preview = json.loads(preview_output.read_text(encoding="utf-8"))
        finally:
            service.shutdown()
            service.deleteLater()
        result = {"designer": designer, "native": native, "isolated_export": exported, "preview_process": preview,
                  "saved_project_roundtrip": True, "existing_projects": compatibility,
                  "registry_fingerprint": registry.fingerprint,
                  "source_fingerprint": source_fingerprint(base)}
        (output / "runtime.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))


if __name__ == "__main__":
    main()
