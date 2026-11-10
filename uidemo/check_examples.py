"""检查设计器打开与撤销，以及每份独立导出的实际交互。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QDialogButtonBox, QLabel, QLineEdit, QWidget
from PySide6.QtGui import QTextDocument

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from core.events import event_bindings, set_event_enabled
from core.storage import load_project
from uidemo.build_examples import EXAMPLES
from widgets.builtin import create_registry


class ErrorLog(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def click(widget):
    position = QPoint(8, widget.height() // 2) if isinstance(widget, QCheckBox) else widget.rect().center()
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=position)
    QApplication.processEvents()


def check_inventory(window):
    c = window.controls
    table = c["stock_list"]
    visible = lambda: [table.topLevelItem(row) for row in range(table.topLevelItemCount())
                       if not table.topLevelItem(row).isHidden()]
    c["search"].setText("扩展坞")
    assert len(visible()) == 1 and visible()[0].text(0) == "1003"
    click(c["reset_button"])
    assert len(visible()) == 8
    click(c["low_only"])
    assert {item.text(0) for item in visible()} == {"1003", "1007"}
    c["category"].setCurrentText("耗材")
    assert len(visible()) == 1 and visible()[0].text(0) == "1007"
    table.setCurrentItem(visible()[0])
    assert "1007" in c["selection"].text()
    c["search"].setText("没有此物品")
    assert not visible() and "共 0 项" in c["result"].text()
    click(c["reset_button"])
    assert len(visible()) == 8


def check_tasks(window):
    c = window.controls
    table = c["task_table"]
    click(c["add_task"])
    assert "请先输入" in c["notice"].text()
    c["task_name"].setText("交互验证.pdf")
    QTest.keyClick(c["task_name"], Qt.Key.Key_Return)
    assert table.rowCount() == 5 and table.item(4, 1).text() == "交互验证.pdf"
    table.selectRow(0)
    click(c["toggle_task"])
    QTest.qWait(480)
    assert c["progress"].value() > 64 and table.item(0, 4).text() == "进行中"
    click(c["toggle_task"])
    paused = c["progress"].value()
    QTest.qWait(480)
    assert c["progress"].value() == paused and table.item(0, 4).text() == "已暂停"
    click(c["clear_done"])
    assert table.rowCount() == 4
    table.selectRow(0)
    click(c["toggle_task"])
    for _ in range(26):
        window._task_demo.advance()
    assert table.item(0, 4).text() == "已完成"
    assert not window._task_demo.timer.isActive()
    click(c["clear_done"])
    assert table.rowCount() == 3


def check_login(window):
    c = window.controls
    click(c["login_button"])
    assert "请填写账号" in c["message"].text()
    c["account"].setText("demo")
    click(c["login_button"])
    assert "请填写密码" in c["message"].text()
    c["password"].setText("wrong")
    click(c["login_button"])
    assert "不匹配" in c["message"].text()
    click(c["fill_demo"])
    click(c["show_password"])
    assert c["password"].echoMode() == QLineEdit.EchoMode.Normal
    QTest.keyClick(c["password"], Qt.Key.Key_Return)
    assert "校验通过" in c["message"].text()
    assert c["password"].text() == "" and c["password"].echoMode() == QLineEdit.EchoMode.Password


def check_settings(window):
    c = window.controls
    tabs = c["settings_tabs"]
    QTest.mouseClick(tabs.tab_bar, Qt.MouseButton.LeftButton, pos=tabs.tab_bar.tabRect(1).center())
    assert tabs.tab_bar.currentIndex() == 1
    click(c["notifications"])
    assert not c["volume"].isEnabled() and not c["quiet_mode"].isEnabled()
    click(c["notifications"])
    c["volume"].setValue(35)
    assert c["volume_value"].text() == "35%"
    c["workspace_name"].clear()
    click(c["apply"])
    assert "不能为空" in c["settings_message"].text() and tabs.tab_bar.currentIndex() == 0
    c["workspace_name"].setText("设计验证工作台")
    c["retention"].setValue(90)
    click(c["apply"])
    assert window._demo_settings["retention"] == 90
    assert "设计验证工作台" in c["settings_summary"].text()
    click(c["restore"])
    assert c["workspace_name"].text() == "我的工作空间" and c["volume"].value() == 60
    click(c["apply"])
    assert window._demo_settings["retention"] == 30


def check_menus(window):
    c = window.controls
    assert len(window.menuBar().actions()) == 3
    c["menu_new"].trigger()
    assert "已新建项目 1" in c["menu_message"].text()
    c["menu_details"].trigger()
    assert c["detail"].isHidden() and not c["menu_details"].isChecked()
    c["menu_details"].trigger()
    assert not c["detail"].isHidden() and c["menu_details"].isChecked()
    c["menu_recent_inventory"].trigger()
    assert "库存管理台" in c["menu_message"].text()
    assert not c["menu_disabled"].isEnabled() and not c["menu_hidden"].isVisible()


def check_text_inputs(window):
    c = window.controls
    window.activateWindow()
    QTest.qWait(50)
    editor = c["editor"]
    editor.selectAll()
    QTest.keyClicks(editor, "A short draft.")
    assert c["reader"].toPlainText().startswith("A short draft.")
    assert "14" in c["statistics"].text()
    c["font_size"].setValue(16)
    assert editor.font().pointSize() == 16
    c["font_picker"].setCurrentIndex((c["font_picker"].currentIndex() + 1) % c["font_picker"].count())
    assert editor.font().family() == c["font_picker"].currentFont().family()
    click(c["read_only"])
    assert editor.isReadOnly()
    c["options"].setChecked(False)
    assert not editor.isReadOnly() and not c["read_only"].isEnabled()
    c["options"].setChecked(True)
    assert editor.isReadOnly() and c["read_only"].isEnabled()
    click(c["read_only"])
    QTest.keyClick(window, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
    QTest.qWait(180)
    assert window._draft_count == 1 and "A short draft." in window._draft_html
    c["shortcut_input"].setFocus()
    QTest.keyClick(c["shortcut_input"], Qt.Key.Key_K,
                   Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    click(c["apply_shortcut"])
    assert c["save_draft"].shortcut().toString() == "Ctrl+Shift+K"
    QTest.keyClick(window, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
    QTest.qWait(180)
    assert window._draft_count == 1
    QTest.keyClick(window, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    QTest.qWait(180)
    assert window._draft_count == 2
    QTest.mouseClick(c["help_link"], Qt.MouseButton.LeftButton, pos=QPoint(8, 14))
    assert "左侧编辑" in c["message"].text()
    reader = c["reader"]
    anchor = next(QPoint(x, y) for y in range(reader.viewport().height())
                  for x in range(0, reader.viewport().width(), 4) if reader.anchorAt(QPoint(x, y)) == "demo:restore")
    QTest.mouseClick(reader.viewport(), Qt.MouseButton.LeftButton, pos=anchor)
    assert "写下今天的想法" in editor.toPlainText()
    assert not c["save_draft"].icon().isNull()


def check_profile(window):
    c = window.controls
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    click(c["nav_home"])
    assert c["title"].text() == "首页" and c["nav_active"].y() == 108
    click(c["nav_tools_one"])
    assert c["tool_caption_1"].text() == "效率工具1"
    click(c["nav_tools_two"])
    assert c["title"].text() == "贰号工具箱" and c["tool_caption_3"].text() == "实用工具3"
    click(c["nav_profile"])
    assert c["title"].text() == "个人中心" and c["nav_active"].y() == 148
    click(c["edit_profile"])
    dialog = window._profile_dialog
    dialog._nickname.clear()
    click(dialog._buttons.button(QDialogButtonBox.StandardButton.Save))
    assert dialog.isVisible() and dialog._message.text() == "昵称不能为空。"
    dialog._nickname.setText("示例用户")
    dialog._location.setText("上海")
    click(dialog._buttons.button(QDialogButtonBox.StandardButton.Save))
    assert c["nickname"].text() == "示例用户" and c["location"].text() == "上海"
    assert c["top_name"].toolTip() == "示例用户"
    click(c["edit_profile"])
    dialog = window._profile_dialog
    dialog._nickname.setText("取消这次修改")
    click(dialog._buttons.button(QDialogButtonBox.StandardButton.Cancel))
    assert c["nickname"].text() == "示例用户"
    for index in range(1, 4):
        click(c[f"tool_{index}"])
        assert window._tool_dialog.text() == f"我喜欢的工具{index}"
        window._tool_dialog.accept()
    click(c["nav_settings"])
    assert window._tool_dialog.windowTitle() == "设置"
    window._tool_dialog.accept()
    click(c["minimize"])
    assert window.isMinimized()
    window.showNormal()
    QApplication.processEvents()
    click(c["close_window"])
    assert not window.isVisible()


CHECKS = (check_inventory, check_tasks, check_login, check_settings, check_menus, check_text_inputs, check_profile)


def check_standalone(base, only=None):
    probe = '''import json, runpy
from PySide6.QtWidgets import QApplication
app = QApplication([])
entry = runpy.run_path("main.py")
window = entry["create_window"](app)
window.show()
app.processEvents()
print(json.dumps({"窗口": window.windowTitle(), "组件数": len(window.controls), "仓库外独立运行": "通过"}, ensure_ascii=False))
window.close()
'''
    results = []
    environment = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "QT_QPA_PLATFORM"):
        environment.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="uidemo_standalone_") as temporary:
        for number, (directory, _, _, _) in enumerate(EXAMPLES, 1):
            if only is not None and only != number:
                continue
            target = Path(temporary) / directory
            shutil.copytree(base / directory / "Python导出", target,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            process = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", probe], cwd=target,
                                     env=environment, check=True, capture_output=True, text=True,
                                     encoding="utf-8", timeout=30)
            result = json.loads(process.stdout)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    from core.storage import atomic_write
    report_base = base / EXAMPLES[only - 1][0] if only is not None else base
    atomic_write(report_base / "独立运行验证.json", json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8"))


def check_export(index, base):
    app = QApplication([])
    folder, title, _, _ = EXAMPLES[index]
    model = load_project(base / folder / (title + ".uipro")).model
    source = (base / folder / (title + ".uipro")).read_bytes()
    entry = base / folder / "Python导出" / "main.py"
    spec = importlib.util.spec_from_file_location("_demo_entry", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors = ErrorLog()
    logging.getLogger().addHandler(errors)
    window = module.create_window(app)
    try:
        window.show()
        app.processEvents()
        if index == 6:
            assert window.grab().save(str(base / folder / "运行预览.png"))
        for node in model.nodes.values():
            widget = window.controls[node.code_name]
            if isinstance(widget, QWidget) and node.slot == "children":
                assert widget.parentWidget().rect().contains(widget.geometry()), f"组件超出父容器：{node.name}"
            if isinstance(widget, QLabel) and widget.text():
                if widget.textFormat() == Qt.TextFormat.RichText:
                    document = QTextDocument()
                    document.setDocumentMargin(0)
                    document.setDefaultFont(widget.font())
                    document.setHtml(widget.text())
                    document.setTextWidth(widget.contentsRect().width())
                    assert document.size().height() <= widget.contentsRect().height(), node.name
                    continue
                flags = Qt.TextFlag.TextWordWrap if widget.wordWrap() else Qt.TextFlag.TextExpandTabs
                bounds = widget.fontMetrics().boundingRect(widget.contentsRect(), int(flags), widget.text())
                assert bounds.height() <= widget.height(), f"标签高度不足：{node.name}"
                if not widget.wordWrap():
                    assert max(widget.fontMetrics().horizontalAdvance(line) for line in widget.text().splitlines()) <= widget.width(), node.name
            if "table_data" in node.properties:
                widths = node.properties["table_data"]["column_widths"]
                assert tuple(widget.columnWidth(column) for column in range(len(widths))) == tuple(widths)
        CHECKS[index](window)
        assert not errors.messages, errors.messages
        assert (base / folder / (title + ".uipro")).read_bytes() == source
        return {"名称": title, "独立导出运行": "通过", "实际交互": "通过", "组件边界与文字尺寸": "通过",
                "原设计文件保持不变": "通过", "平台": app.platformName(), "设备像素比": window.devicePixelRatioF()}
    finally:
        if hasattr(window, "_task_demo"):
            window._task_demo.timer.stop()
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        logging.getLogger().removeHandler(errors)


def check_designer(base, only=None):
    app = QApplication([])
    initialize(app, configure_logging=False)
    registry = create_registry()
    with tempfile.TemporaryDirectory(prefix="uidemo_settings_") as temp:
        settings = QSettings(str(Path(temp) / "settings.ini"), QSettings.Format.IniFormat)
        window = MainWindow(registry, settings=settings, enable_recovery=False, persist_settings=False)
        try:
            window.resize(1320, 900)
            window.show()
            selected = EXAMPLES if only is None else (EXAMPLES[only - 1],)
            for folder, title, _, _ in selected:
                path = base / folder / (title + ".uipro")
                document = window.open_path(path)
                before = document.model
                node = next(node for node in before.nodes.values() if node.code_name == "title")
                document.execute("示例标题修改", lambda model: set_property(model, registry, node.id, "text", "可继续编辑"))
                assert document.model.nodes[node.id].properties["text"] == "可继续编辑"
                document.undo()
                assert document.model == before
                event = event_bindings(before, registry)[0]
                key = next(node.id for node in before.nodes.values() if node.code_name == event["control"])
                document.execute("示例事件取消", lambda model: set_event_enabled(model, registry, key, event["key"], False))
                assert len(event_bindings(document.model, registry)) == len(event_bindings(before, registry)) - 1
                document.undo()
                assert document.model == before
                window.page.canvas.fit_to_window()
                app.processEvents()
                QTest.qWait(60)
                assert window.grab().save(str(base / folder / "设计器.png"))
            return {f"设计器打开 {len(selected)} 份项目": "通过", "属性编辑与撤销": "通过", "事件勾选与撤销": "通过"}
        finally:
            window.discard_all_for_test()
            window.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=int, choices=range(len(EXAMPLES)))
    parser.add_argument("--designer", action="store_true")
    parser.add_argument("--standalone", action="store_true")
    parser.add_argument("--base", type=Path, default=Path(__file__).parent)
    parser.add_argument("--only", type=int, choices=range(1, len(EXAMPLES) + 1), help="只检查指定示例")
    args = parser.parse_args()
    if args.standalone:
        check_standalone(args.base.resolve(), args.only)
        return
    if args.worker is not None:
        print(json.dumps(check_export(args.worker, args.base.resolve()), ensure_ascii=False))
        return
    if args.designer:
        print(json.dumps(check_designer(args.base.resolve(), args.only), ensure_ascii=False))
        return
    environment = os.environ.copy()
    environment.pop("QT_QPA_PLATFORM", None)
    results = []
    indices = range(len(EXAMPLES)) if args.only is None else (args.only - 1,)
    for option in (["--worker", str(index)] for index in indices):
        result = subprocess.run([sys.executable, "-X", "utf8", __file__, "--base", str(args.base), *option],
                                env=environment, check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
        results.append(json.loads(result.stdout))
        print(result.stdout.strip(), flush=True)
    selection = [] if args.only is None else ["--only", str(args.only)]
    result = subprocess.run([sys.executable, "-X", "utf8", __file__, "--base", str(args.base), "--designer", *selection],
                            env=environment, check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    results.append(json.loads(result.stdout))
    print(result.stdout.strip(), flush=True)
    from core.storage import atomic_write
    report_base = args.base / EXAMPLES[args.only - 1][0] if args.only is not None else args.base
    atomic_write(report_base / "验证结果.json", json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
