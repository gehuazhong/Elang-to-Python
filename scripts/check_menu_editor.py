"""打开真实菜单编辑器和示例菜单，生成可复核截图。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.storage import load_project
from panels.menu_editor import MenuEditor
from runtime.application import configure_application
from runtime.builder import RuntimeTree
from widgets.builtin import create_registry


def main():
    app = QApplication.instance() or QApplication([])
    configure_application(app)
    registry = create_registry()
    folder = ROOT / "uidemo/05_菜单编辑示例"
    model = load_project(folder / "菜单编辑示例.uipro").model
    shell = MainWindow(registry, persist_settings=False, enable_recovery=False)
    editor = MenuEditor(model, registry, shell, selected_id=next(node.id for node in model.nodes.values() if node.code_name == "menu_details"))
    tree = RuntimeTree(registry, design_mode=False)
    try:
        editor.show()
        QTest.qWait(150)
        assert editor.grab().save(str(folder / "菜单编辑器.png"))
        editor.hide()
        tree.apply(compile_plan(model, registry, "菜单截图"))
        root = tree.root
        root.show()
        root.activateWindow()
        QTest.qWait(100)
        bar = root.menuBar()
        file_action = bar.actions()[0]
        QTest.mouseClick(bar, Qt.MouseButton.LeftButton, pos=bar.actionGeometry(file_action).center())
        menu = file_action.menu()
        QTest.qWait(100)
        assert menu.isVisible()
        screenshot = root.grab()
        painter = QPainter(screenshot)
        try:
            painter.drawPixmap(root.mapFromGlobal(menu.mapToGlobal(QPoint())), menu.grab())
        finally:
            painter.end()
        assert screenshot.save(str(folder / "菜单展开.png"))
        new_action = menu.actions()[0]
        fired = []
        new_action.triggered.connect(lambda checked=False: fired.append(checked))
        QTest.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(new_action).center())
        assert fired == [False] and not menu.isVisible()
        print("Windows 菜单编辑器截图、菜单展开与鼠标点击通过。")
    finally:
        editor.close()
        editor.deleteLater()
        tree.dispose()
        shell.discard_all_for_test()
        shell.close()


if __name__ == "__main__":
    main()
