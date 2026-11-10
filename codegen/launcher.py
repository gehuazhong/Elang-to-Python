"""导出应用的稳定入口；重复导出只发布新版本指针。"""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path
import re
import sys
from types import ModuleType

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QCoreApplication, Qt


def load_module(name: str, path: Path, *, package: bool = False) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path, submodule_search_locations=[str(path.parent)] if package else None)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载导出的界面模块。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def create_window(application: QApplication) -> QMainWindow:
    base = Path(__file__).resolve().parent
    # 指针只读一次，确保本次运行的所有文件都来自同一个完整版本。
    pointer = json.loads((base / "current.json").read_text(encoding="utf-8"))
    if not isinstance(pointer, dict) or pointer.get("protocol") != 1 or not isinstance(pointer.get("version"), str) or not re.fullmatch(r"[0-9a-f]{64}", pointer["version"]):
        raise RuntimeError("导出版本指针无效，请重新导出到新目录。")
    module = load_module("_uiplay_ui_" + pointer["version"], base / "generated" / pointer["version"] / "ui_main.py", package=True)
    module.configure_application(application)
    window = module.create_window()
    try:
        # 以业务文件所在目录为搜索起点，支持同目录的自有模块。
        if str(base) not in sys.path:
            sys.path.insert(0, str(base))
        business = load_module("_uiplay_business", base / "handlers.py")
        connect_events = getattr(business, "connect_events", None)
        if not callable(connect_events):
            raise RuntimeError("业务文件缺少可调用的 connect_events 函数。")
        connect_events(window)
    except Exception:
        window.close()
        window.deleteLater()
        raise
    return window


def main() -> int:
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    application = QApplication(sys.argv)
    try:
        window = create_window(application)
        window.show()
        return application.exec()
    except Exception:
        logging.getLogger(__name__).exception("导出应用启动失败。")
        box = QMessageBox()
        box.setWindowTitle("启动失败")
        box.setText("界面未能启动，请检查导出文件、运行依赖与业务代码。")
        box.addButton("关闭", QMessageBox.ButtonRole.AcceptRole)
        box.exec()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
