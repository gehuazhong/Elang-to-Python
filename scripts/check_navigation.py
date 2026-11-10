"""Build a sidebar example and check native and isolated exported navigation."""

import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from uuid import uuid4

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt, QTimer
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication


def check_window(window, controls, output):
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
    window.show()
    QApplication.processEvents()
    tabs = controls["tab_widget_1"]
    names = ("button_2", "button_3", "button_4")
    buttons = [controls[name] for name in names]
    sidebar = controls["frame_2"]
    switches = QSignalSpy(tabs.currentChanged)
    for index in (0, 1, 2, 0):
        button = buttons[index]
        for x in (20, 100, 165):
            point = QPoint(x, button.y() + 20)
            hit = sidebar.childAt(point)
            assert hit is button, (index, x, type(hit).__name__)
            QTest.mouseClick(hit, Qt.MouseButton.LeftButton, pos=hit.mapFrom(sidebar, point))
            assert tabs.tab_bar.currentIndex() == index
            assert [item.property("uiplayNavigationActive") for item in buttons] == [i == index for i in range(3)]
        QApplication.processEvents()
        assert window.grab().save(str(output / f"page-{index + 1}.png"))
    assert switches.count() == 3
    assert tabs.tab_bar.isHidden()
    for index in range(60):
        buttons[index % 3].click()
        assert tabs.tab_bar.currentIndex() == index % 3
    return {"platform": QApplication.platformName(), "click_positions_checked": 12,
            "repeated_switches": 60, "active_state_synchronized": True, "hidden_tab_header": True}


def main():
    app = QApplication([])
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        entry, output = Path(sys.argv[2]), Path(sys.argv[3])
        module = runpy.run_path(str(entry), run_name="navigation_export_check")
        window = module["create_window"](app)
        try:
            result = check_window(window, window.controls, output)
        finally:
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert not any(name == "core" or name.startswith("core.") or name == "designer" or name.startswith("designer.")
                       for name in sys.modules)
        print(json.dumps(result, ensure_ascii=True))
        return

    from runtime.application import configure_application
    configure_application(app)
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        from preview.worker import Worker
        output = Path(sys.argv[2])

        class NavigationProbe(Worker):
            def send(self, kind, **values):
                super().send(kind, **values)
                if kind == "ready":
                    QTimer.singleShot(100, self.check)

            def check(self):
                try:
                    tree = self.runtime.tree
                    controls = {node.code_name: tree.widgets[key] for key, node in tree.plans.items()}
                    result = check_window(tree.root, controls, output)
                    (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
                    tree.root.close()
                except Exception as error:
                    self.fail(str(error))

        raise SystemExit(NavigationProbe(app, sys.stdout.buffer).run())

    from dataclasses import replace
    from codegen.publisher import export_project
    from core.build_plan import compile_plan
    from core.commands.arrange import stack_nodes
    from core.commands.nodes import set_property
    from core.storage import commit_project, load_project
    from runtime.builder import RuntimeTree, verify_registry
    from preview.service import PreviewService
    from widgets.builtin import create_registry

    base = Path(__file__).resolve().parents[1]
    output = base / "reports" / "navigation-20261111"
    output.mkdir(parents=True, exist_ok=True)
    source = base / "uidemo/08_万金油UI/万金油UI.uipro"
    reference = base / "uidemo/07_兔子工具个人中心/兔子工具个人中心.uipro"
    hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (source, reference)}
    example = source.with_name("万金油UI_导航增强.uipro")
    registry = create_registry()
    verify_registry(registry)
    model = load_project(source).model
    codes = {node.code_name: node.id for node in model.nodes.values()}
    model = replace(model, data=model.data.changed(document_id=str(uuid4()), name="万金油UI_导航增强"))
    for number in (2, 3, 4):
        key = codes[f"button_{number}"]
        model = set_property(model, registry, key, "navigation_page", f"tab_page_{number - 1}")
        model = set_property(model, registry, key, "navigation_style", "sidebar")
        model = set_property(model, registry, key, "cursor_shape", "pointing_hand")
    model = stack_nodes(model, tuple(codes[f"button_{number}"] for number in (2, 3, 4)), "front")
    model = set_property(model, registry, codes["tab_widget_1"], "header_visible", False)
    model = set_property(model, registry, codes["tab_widget_1"], "current_index", 0)
    for number, title in enumerate(("用户中心", "任务中心", "软件设置"), 1):
        model = set_property(model, registry, codes[f"tab_page_{number}"], "text", title)
    registry.validate(model)
    if not example.exists():
        commit_project(example, model, expected_token=None)
    else:
        model = load_project(example).model
    native_output = output / "native"
    native_output.mkdir(exist_ok=True)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        plan = compile_plan(model, registry, "navigation native check")
        for _ in range(6):
            tree.apply(plan)
        controls = {node.code_name: tree.widgets[node.id] for node in model.nodes.values()}
        native_result = check_window(tree.root, controls, native_output)
    finally:
        tree.dispose()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    entry = export_project(model, registry, output / "export")
    export_output = output / "exported"
    export_output.mkdir(exist_ok=True)
    process = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--export", str(entry), str(export_output)],
                             cwd=entry.parent, env={**os.environ, "QT_QPA_PLATFORM": app.platformName()},
                             capture_output=True, text=True, encoding="utf-8", timeout=90)
    if process.returncode:
        raise RuntimeError(process.stdout + process.stderr)
    exported_result = json.loads(process.stdout.strip().splitlines()[-1])
    preview_output = output / "preview"
    preview_output.mkdir(exist_ok=True)
    service = PreviewService(registry)
    service._command = lambda: (sys.executable, ["-X", "utf8", "-u", "-m", "scripts.check_navigation",
                                               "--preview", str(preview_output)])
    try:
        service.start(model, "navigation-check", "navigation-check-session")
        for _ in range(1000):
            QTest.qWait(20)
            if not service.active:
                break
        assert not service.active and service.last_ready and not service.last_error, service.last_error
        assert service.last_ready["process_id"] != os.getpid()
        preview_result = json.loads((preview_output / "result.json").read_text(encoding="utf-8"))
    finally:
        service.shutdown()
        service.deleteLater()
    for path, digest in hashes.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        original = load_project(path).model
        compile_plan(original, registry, "backward compatibility")
    result = {"native": native_result, "isolated_export": exported_result, "preview_process": preview_result,
              "original_projects_unchanged": {str(path.relative_to(base)): digest for path, digest in hashes.items()},
              "example": str(example.relative_to(base)), "export": str(entry.relative_to(base))}
    (output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
