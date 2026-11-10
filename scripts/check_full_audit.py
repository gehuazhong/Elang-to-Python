"""核对模型视图的 Windows 运行、独立导出和选择模型释放。"""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.models import thaw
from core.storage import atomic_write
from runtime.application import configure_application
from runtime.builder import RuntimeTree
from uidemo.build_examples import Design


CHECK = '''
from PySide6.QtCore import QCoreApplication, QEvent, QItemSelectionModel, Qt
def check(controls, values, app):
    result = {}
    for name, options in values.items():
        widget = controls[name]
        original, selection = widget.model(), widget.selectionModel()
        index = original.index(0, 0)
        original.setData(index, "runtime edit")
        selection.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        widget.configure({**options, "alternating": not options["alternating"]})
        assert widget.model() is original and widget.selectionModel() is selection
        assert widget.model().index(0, 0).data() == "runtime edit"
        assert widget.selectionModel().currentIndex() == index
        count = lambda: len(widget.findChildren(QItemSelectionModel, options=Qt.FindChildOption.FindDirectChildrenOnly))
        baseline = count()
        for number in range(20):
            candidate = dict(options)
            if "items" in options:
                candidate["items"] = [str(number)]
            elif "table_data" in options:
                candidate["table_data"] = {"headers": ["Name"], "rows": [[str(number)]]}
            else:
                candidate["tree_data"] = [{"text": str(number), "children": []}]
            widget.configure(candidate)
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
        assert count() == baseline, (name, baseline, count())
        assert widget.model().index(0, 0).data() == "19"
        result[name] = {"style_keeps_selection_and_edits": True, "selection_models_before": baseline,
                        "selection_models_after_20_replacements": count()}
    return result
'''


def main():
    app = QApplication([])
    configure_application(app)
    d = Design("模型视图稳定性检查", 900, 550)
    for index, kind in enumerate(("list_view", "table_view", "tree_view", "column_view")):
        x, y = 20 + index % 2 * 440, 60 + index // 2 * 240
        d.label("title_" + kind, d.registry.require("builtin." + kind).label, x, y - 32, 410)
        d.add(kind, kind, kind, x, y, 420, 195)
    model = d.finish()
    output = ROOT / "reports/full-audit-20261110"
    output.mkdir(parents=True, exist_ok=True)
    values = {node.code_name: thaw(d.registry.require(node.type_id).defaults().changed(**node.properties))
              for node in model.nodes.values() if node.code_name in {"list_view", "table_view", "tree_view", "column_view"}}
    namespace = {}
    exec(CHECK, namespace)
    tree = RuntimeTree(d.registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, d.registry, "native audit"))
        tree.root.show()
        app.processEvents()
        controls = {node.code_name: tree.widgets[node.id] for node in model.nodes.values()}
        assert tree.root.grab().save(str(output / "model-views.png"))
        native = namespace["check"](controls, values, app)
    finally:
        tree.dispose()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    entry = export_project(model, d.registry, output / "e")
    payload = output / "view-options.json"
    atomic_write(payload, json.dumps(values, ensure_ascii=False).encode("utf-8"))
    probe = CHECK + '''
import json, runpy, sys
from PySide6.QtWidgets import QApplication
app = QApplication([])
window = runpy.run_path(sys.argv[1])["create_window"](app)
window.show()
app.processEvents()
with open(sys.argv[2], encoding="utf-8") as stream:
    result = check(window.controls, json.load(stream), app)
assert not any(name in sys.modules for name in ("app", "core", "runtime", "widgets"))
window.close()
window.deleteLater()
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
print(json.dumps(result))
'''
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="audit_export_") as temporary:
        completed = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", probe, str(entry), str(payload)],
                                  cwd=temporary, env=environment, text=True, capture_output=True, timeout=30)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = {"platform": app.platformName(), "native": native, "isolated_export": json.loads(completed.stdout)}
    atomic_write(output / "desktop.json", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
