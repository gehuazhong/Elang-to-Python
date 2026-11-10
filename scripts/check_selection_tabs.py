"""生成选择夹对照示例，检查 Windows 页签交互并保存截图。"""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPointF, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.storage import atomic_write, commit_project, load_project
from runtime.builder import RuntimeTree
from uidemo.build_examples import Design
from widgets.builtin import create_registry
from widgets.support import support_markdown


def example():
    d = Design("选择夹 · 表头与页面", 1000, 752, "#f4f5f7")
    d.label("title", "选择夹表头与页面", 24, 16, 800, 36, size=19, bold=True)
    d.label("intro", "顶部、底部、左侧、右侧，以及隐藏表头后的完整内容区。", 24, 52, 930, 25, color="#68717d")
    for index, (position, label) in enumerate((("top", "顶部"), ("bottom", "底部"), ("left", "左侧"), ("right", "右侧"))):
        x, y = 24 + index % 2 * 484, 96 + index // 2 * 230
        code = "tabs_" + position
        d.label("caption_" + position, label + "表头", x, y, 450, 24, bold=True)
        d.add("tab_widget", code, label + "选择夹", x, y + 32, 460, 184,
              tab_position=position, tab_bar_size=36, tabs_closable=True, movable=True,
              tab_shape="triangular" if position == "bottom" else "rounded")
        a, b = d.tab_pages(code, label + "信息", label + "设置")
        d.label("page_" + position, "当前是基本信息页", 18, 18, 300, 28, size=12, bold=True, parent=a)
        d.add("line_edit", "input_" + position, label + "输入框", 18, 60, 280, 32,
              parent=a, placeholder_text="页面内容跟随表头方向排列")
        d.label("second_" + position, "这里是第二页，可继续放置控件。", 18, 22, 330, 32, parent=b)
        d.event(code, "tabCloseRequested")
        d.event(code, "tabMoved")
    d.label("hidden_caption", "隐藏表头 + 关闭页面边框", 24, 562, 920, 24, bold=True)
    d.add("tab_widget", "tabs_hidden", "隐藏表头选择夹", 24, 594, 944, 132,
          header_visible=False, pane_border=False)
    a, b = d.tab_pages("tabs_hidden", "内容一", "内容二")
    d.label("hidden_title", "内容区从左上角开始，不保留表头空位。", 18, 14, 850, 32, size=12, bold=True, parent=a)
    d.label("hidden_note", "在设计器的对象树选择页面，或用“页面 → 当前页”切换。", 18, 54, 850, 28, parent=a)
    d.label("hidden_second", "隐藏表头后仍然可以切换到第二页。", 18, 24, 850, 32, parent=b)
    return d.finish()


def main():
    app = QApplication([])
    initialize(app, configure_logging=False)
    registry = create_registry()
    output = ROOT / "reports/selection-tabs"
    output.mkdir(parents=True, exist_ok=True)
    path = ROOT / "examples/选择夹表头与页面.uipro"
    if not path.exists():
        commit_project(path, example(), expected_token=None)
    model = load_project(path).model
    tree = RuntimeTree(registry, design_mode=False)
    results = {"platform": app.platformName()}
    try:
        tree.apply(compile_plan(model, registry, "表头检查"))
        tree.root.show()
        QTest.qWait(100)
        assert tree.root.grab().save(str(output / "preview.png"))
        for node in model.nodes.values():
            if node.type_id != "builtin.tab_widget":
                continue
            tabs = tree.widgets[node.id]
            if tabs.tab_bar.isHidden():
                assert tabs.pages[0].geometry() == tabs.rect()
                tabs.set_current_page(1)
                assert tabs.pages[1].isVisible()
            else:
                QTest.mouseClick(tabs.tab_bar, Qt.MouseButton.LeftButton, pos=tabs.tab_bar.tabRect(1).center())
                assert tabs.tab_bar.currentIndex() == 1 and tabs.pages[1].isVisible()
        results["native_page_switches"] = "passed"
    finally:
        tree.dispose()
    entry = export_project(model, registry, output / "export")
    probe = '''import runpy, sys
from PySide6.QtWidgets import QApplication
app = QApplication([])
window = runpy.run_path(sys.argv[1])["create_window"](app)
window.show()
app.processEvents()
assert window.controls["tabs_hidden"].tab_bar.isHidden()
assert window.controls["tabs_left"].tab_bar.width() == 36
assert not any(name in sys.modules for name in ("core", "runtime", "widgets", "app"))
window.close()
print("passed")
'''
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="tabs_check_") as temporary:
        completed = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", probe, str(entry)],
            cwd=temporary, env=environment, capture_output=True, text=True, timeout=30)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        results["isolated_export"] = "passed"
        settings = QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat)
        window = MainWindow(registry, settings=settings, enable_recovery=False, persist_settings=False)
        try:
            window.resize(1540, 990)
            window.show()
            document = window.open_path(path)
            selected = next(node.id for node in document.model.nodes.values() if node.code_name == "tabs_left")
            document.select(selected)
            window.page.canvas.fit_to_window()
            QTest.qWait(100)
            assert "header_visible" in window.properties.editors and "tab_position" in window.properties.editors
            native = window.page.canvas.renderer.tree.widgets[selected]
            local = native.tab_bar.mapTo(native, native.tab_bar.tabRect(1).center())
            scene = window.page.canvas.renderer.items[selected].mapToScene(QPointF(local))
            QTest.mouseClick(window.page.canvas.viewport(), Qt.MouseButton.LeftButton, pos=window.page.canvas.mapFromScene(scene))
            assert document.model.nodes[selected].properties["current_index"] == 1
            document.undo()
            QTest.qWait(50)
            assert window.grab().save(str(output / "designer.png"))
            results["designer_properties_click_and_undo"] = "passed"
        finally:
            window.discard_all_for_test()
            window.close()
    atomic_write(ROOT / "docs/组件支持矩阵.md", support_markdown(registry).encode("utf-8"))
    atomic_write(output / "verification.json", json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
