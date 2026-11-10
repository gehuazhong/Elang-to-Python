"""Run real Windows graphics and Chromium checks, including independent export."""

from pathlib import Path
import argparse
import importlib.util
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QCoreApplication, Qt, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preview", "export"), default="preview")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/components-completion")
    parser.add_argument("--completed-properties", action="store_true", help="Check non-default options and live updates")
    args = parser.parse_args()
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication([])
    from runtime.application import configure_application
    from runtime.builder import RuntimeTree
    from runtime.advanced_widgets import start_advanced
    from widgets.builtin import create_registry
    from core.models import new_project
    from core.commands.nodes import create_node, set_property
    from core.build_plan import compile_plan
    from core.storage import commit_project, load_project
    from codegen.publisher import export_project
    configure_application(app)
    registry = create_registry()
    model = new_project("扩展组件验收")
    model = set_property(model, registry, model.root_id, "geometry.width", 1000)
    model = set_property(model, registry, model.root_id, "geometry.height", 650)
    keys = {}
    positions = {"web_view": (20, 20, 610, 270), "svg_widget": (650, 20, 320, 270),
                 "opengl_widget": (20, 310, 295, 250), "rhi_widget": (335, 310, 295, 250),
                 "graphics_view": (650, 310, 320, 250)}
    for kind, (x, y, width, height) in positions.items():
        model, key = create_node(model, registry, "builtin." + kind, x, y)
        keys[kind] = key
        model = set_property(model, registry, key, "geometry.width", width)
        model = set_property(model, registry, key, "geometry.height", height)
    model = set_property(model, registry, keys["web_view"], "html",
        "<!doctype html><meta charset='utf-8'><title>Native Web Check</title>"
        "<style>body{font:18px 'Microsoft YaHei UI';padding:24px;color:#243444}h1{color:#0078d4}</style>"
        "<h1>网页控件已加载</h1><p>原生 Chromium · JavaScript · 独立导出</p>"
        "<script>window.uiplayCheck=6*7</script>")
    model = set_property(model, registry, keys["opengl_widget"], "clear_color", "#246b92")
    model = set_property(model, registry, keys["rhi_widget"], "clear_color", "#266c58")
    args.output.mkdir(parents=True, exist_ok=True)
    project_path = args.output / "扩展组件示例.uipro"
    if not project_path.exists():
        commit_project(project_path, model, expected_token=None)
    else:
        model = load_project(project_path).model
        keys = {kind: next(node.id for node in model.nodes.values() if node.type_id == "builtin." + kind) for kind in positions}
    if args.completed_properties:
        for kind, values in {
            "web_view": {"auto_load_images": False, "local_storage": False, "pdf_viewer": False,
                         "page_background": "#f4f5f7", "default_font_size": 19, "minimum_font_size": 12},
            "opengl_widget": {"update_behavior": "partial"},
            "rhi_widget": {"mirror_vertically": True},
            "svg_widget": {"keep_aspect_ratio": True, "animation_enabled": False},
            "graphics_view": {"antialiasing": True, "scene_background": "#f4f5f7", "scene_text_color": "#246b92"},
        }.items():
            for key, value in values.items():
                model = set_property(model, registry, keys[kind], key, value)
    tree = None
    if args.mode == "preview":
        tree = RuntimeTree(registry, design_mode=False)
        tree.apply(compile_plan(model, registry, "native"))
        window = tree.root
        controls = {kind: tree.widgets[key] for kind, key in keys.items()}
    else:
        entry = export_project(model, registry, args.output / "graphics-export")
        spec = importlib.util.spec_from_file_location("advanced_export", entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        window = module.create_window(app)
        controls = {kind: window.controls[model.nodes[key].code_name] for kind, key in keys.items()}
    report = {"mode": args.mode, "platform": app.platformName(), "signals": {}, "errors": []}
    for kind in ("opengl_widget", "rhi_widget"):
        report["signals"][kind] = {"initialized": 0, "rendered": 0}
        for event in ("initialized", "rendered"):
            def count(k=kind, e=event):
                report["signals"][k][e] += 1
            getattr(controls[kind], event).connect(count)
        controls[kind].failed.connect(report["errors"].append)
    controls["web_view"].loadFinished.connect(lambda ok: report.update(web_loaded=ok))
    if tree:
        start_advanced(tree.widgets)
    window.show()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        QTest.qWait(50)
        if report.get("web_loaded") and all(item["rendered"] for item in report["signals"].values()):
            break
    javascript = []
    controls["web_view"].native.page().runJavaScript("window.uiplayCheck", javascript.append)
    deadline = time.monotonic() + 5
    while not javascript and time.monotonic() < deadline:
        QTest.qWait(50)
    report["javascript"] = javascript
    report["web_title"] = controls["web_view"].native.title()
    report["opengl_pixel"] = controls["opengl_widget"].native.grabFramebuffer().pixelColor(40, 40).name()
    report["rhi_pixel"] = controls["rhi_widget"].native.grabFramebuffer().pixelColor(40, 40).name()
    if args.completed_properties:
        from PySide6.QtWebEngineCore import QWebEngineSettings
        from PySide6.QtOpenGLWidgets import QOpenGLWidget
        from PySide6.QtGui import QPainter
        web = controls["web_view"]
        settings = web.native.settings()
        attributes = ("AutoLoadImages", "LocalStorageEnabled", "PdfViewerEnabled")
        options = {
            "web_attributes": all(not settings.testAttribute(getattr(QWebEngineSettings.WebAttribute, name)) for name in attributes),
            "web_fonts": settings.fontSize(QWebEngineSettings.FontSize.DefaultFontSize) == 19
                         and settings.fontSize(QWebEngineSettings.FontSize.MinimumFontSize) == 12,
            "web_background": web.native.page().backgroundColor().name() == "#f4f5f7",
            "opengl_partial": controls["opengl_widget"].native.updateBehavior() == QOpenGLWidget.UpdateBehavior.PartialUpdate,
            "rhi_mirror": controls["rhi_widget"].native.isMirrorVerticallyEnabled(),
            "svg_ratio": controls["svg_widget"].native.renderer().aspectRatioMode() == Qt.AspectRatioMode.KeepAspectRatio,
            "svg_animation": not controls["svg_widget"].native.renderer().isAnimationEnabled(),
            "scene_antialiasing": bool(controls["graphics_view"].renderHints() & QPainter.RenderHint.Antialiasing),
            "scene_background": controls["graphics_view"].backgroundBrush().color().name() == "#f4f5f7",
        }
        reloads = []
        web.loadStarted.connect(lambda: reloads.append(True))
        web.configure({**web.values, "auto_load_images": True, "local_storage": True, "pdf_viewer": True,
                       "default_font_size": 21, "minimum_font_size": 10, "page_background": "#ffffff"})
        controls["opengl_widget"].configure({**controls["opengl_widget"].values, "update_behavior": "full"})
        controls["rhi_widget"].configure({**controls["rhi_widget"].values, "mirror_vertically": False})
        QTest.qWait(100)
        options["live_web_update"] = (all(settings.testAttribute(getattr(QWebEngineSettings.WebAttribute, name)) for name in attributes)
                                      and settings.fontSize(QWebEngineSettings.FontSize.DefaultFontSize) == 21
                                      and settings.fontSize(QWebEngineSettings.FontSize.MinimumFontSize) == 10
                                      and web.native.page().backgroundColor().name() == "#ffffff" and not reloads)
        options["live_gpu_update"] = (controls["opengl_widget"].native.updateBehavior() == QOpenGLWidget.UpdateBehavior.NoPartialUpdate
                                      and not controls["rhi_widget"].native.isMirrorVerticallyEnabled())
        report["completed_properties"] = options
    window.grab().save(str(args.output / (args.mode + "-native.png")))
    report["passed"] = (report.get("web_loaded") is True and javascript == [42]
                         and report["opengl_pixel"] == "#246b92" and report["rhi_pixel"] == "#266c58"
                         and all(item["rendered"] > 0 for item in report["signals"].values()) and not report["errors"]
                         and all(report.get("completed_properties", {}).values()))
    (args.output / (args.mode + "-native.json")).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    window.close()
    if tree:
        tree.dispose()
    else:
        window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    print(json.dumps(report, ensure_ascii=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
