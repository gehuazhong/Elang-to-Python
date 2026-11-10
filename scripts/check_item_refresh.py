"""Check item reuse in native windows and in an isolated exported project."""

from pathlib import Path
import json
import os
import runpy
import subprocess
import sys
import tempfile
from time import perf_counter
from types import SimpleNamespace

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid


def check(controls, options, adapters):
    result = {}
    for name, option in options.items():
        widget, values, bindings = controls[option["code_name"]], option["values"], option["bindings"]

        def refresh(candidate):
            adapters._apply_widget_properties(widget, candidate, bindings)
            adapters._apply_easy_properties(widget, candidate)
            adapters._apply_completed_properties(widget, candidate)
            adapters._apply_appearance(widget, candidate)

        item = None
        if name == "combo_box":
            widget.setCurrentIndex(1)
        else:
            item = (widget.item(0) if name == "list_widget" else widget.item(0, 0)
                    if name == "table_widget" else widget.topLevelItem(0))
            widget.setCurrentItem(item)
            if name in {"tree_widget", "super_list"}:
                item.setText(0, "runtime edit")
            else:
                item.setText("runtime edit")
            if name == "tree_widget":
                item.setExpanded(False)
            if name == "super_list":
                item.setCheckState(0, Qt.CheckState.Checked)
        resets = QSignalSpy(widget.model().modelReset)
        started = perf_counter()
        for index in range(20):
            candidate = {**values, "foreground_color": "#246b92" if index % 2 else "#345678"}
            if "table_data" in values:
                candidate["table_data"] = {**values["table_data"],
                                           "column_widths": [80 + index] * len(values["table_data"]["headers"])}
            refresh(candidate)
            if item is None:
                assert widget.currentIndex() == 1
            else:
                assert isValid(item) and widget.currentItem() is item
                text = item.text(0) if name in {"tree_widget", "super_list"} else item.text()
                assert text == "runtime edit"
                if name == "tree_widget":
                    assert not item.isExpanded()
                if name == "super_list":
                    assert item.checkState(0) == Qt.CheckState.Checked
        assert resets.count() == 0, name
        elapsed = round((perf_counter() - started) * 1000, 3)
        # Mutate the caller's plain data in place to verify independent cache keys.
        if "items" in values:
            values["items"][0] = "updated content"
        elif "table_data" in values:
            values["table_data"]["rows"][0][0] = "updated content"
        else:
            values["tree_data"][0]["text"] = "updated content"
        refresh(values)
        assert widget.model().index(0, 0).data() == "updated content"
        if item is not None:
            assert not isValid(item)
        result[name] = {"style_refreshes": 20, "model_resets_during_style": 0,
                        "selection_and_edits_preserved": True, "content_replacement": True,
                        "style_refresh_ms": elapsed}
    return result


def main():
    app = QApplication([])
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        entry, payload = Path(sys.argv[2]), Path(sys.argv[3])
        window = runpy.run_path(str(entry))["create_window"](app)
        try:
            window.show()
            app.processEvents()
            adapters = sys.modules[type(window).__module__]
            result = check(window.controls, json.loads(payload.read_text(encoding="utf-8")), adapters)
            assert not any(name in sys.modules for name in ("app", "core", "runtime", "widgets"))
            print(json.dumps(result))
        finally:
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        return

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from codegen.publisher import export_project
    from core.build_plan import compile_plan
    from core.commands.nodes import create_node, set_property
    from core.models import new_project, thaw
    from core.storage import atomic_write
    from runtime.application import configure_application
    from runtime.appearance import apply_appearance
    from runtime.builder import RuntimeTree
    from runtime.easy_widgets import apply_easy_properties
    from runtime.property_completion import apply_completed_properties
    from runtime.widget_properties import apply_widget_properties
    from widgets.builtin import create_registry

    configure_application(app)
    registry, model, keys, options = create_registry(), new_project("Item refresh audit"), {}, {}
    for index, kind in enumerate(("list_widget", "table_widget", "tree_widget", "super_list", "combo_box")):
        model, key = create_node(model, registry, "builtin." + kind, 20 + index % 2 * 380, 20 + index // 2 * 200)
        if kind == "super_list":
            model = set_property(model, registry, key, "checkboxes", True)
        keys[kind] = key
        spec = registry.require(model.nodes[key].type_id)
        options[kind] = {"code_name": model.nodes[key].code_name,
                         "values": thaw(spec.defaults().changed(**model.nodes[key].properties)),
                         "bindings": [(prop.key, prop.qt_name, prop.label) for prop in spec.properties]}
    output = root / "reports/full-audit-20261111"
    output.mkdir(parents=True, exist_ok=True)
    payload = output / "item-options.json"
    atomic_write(payload, json.dumps(options, ensure_ascii=False).encode("utf-8"))
    adapters = SimpleNamespace(_apply_widget_properties=apply_widget_properties,
                               _apply_easy_properties=apply_easy_properties,
                               _apply_completed_properties=apply_completed_properties,
                               _apply_appearance=apply_appearance)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "audit"))
        tree.root.show()
        app.processEvents()
        native = check({model.nodes[key].code_name: tree.widgets[key] for key in keys.values()}, options, adapters)
        assert tree.root.grab().save(str(output / "item-views.png"))
    finally:
        tree.dispose()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    export_directory = Path(tempfile.mkdtemp(prefix="item-export-", dir=output))
    entry = export_project(model, registry, export_directory)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="item_refresh_") as temporary:
        completed = subprocess.run([sys.executable, "-I", "-X", "utf8", str(Path(__file__).resolve()),
                                    "--export", str(entry), str(payload)],
                                   cwd=temporary, env=environment, capture_output=True, text=True, timeout=45)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = {"platform": app.platformName(), "export_entry": str(entry.relative_to(root)),
              "native": native, "isolated_export": json.loads(completed.stdout)}
    atomic_write(output / "desktop.json", json.dumps(report, indent=2).encode("utf-8"))
    print(json.dumps(report))


if __name__ == "__main__":
    main()
