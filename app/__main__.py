"""统一启动逻辑，支持根目录脚本与应用包两种入口。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QTimer, QCoreApplication, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from core.commands.nodes import set_property
from core.errors import DesignerError
from runtime.builder import verify_registry
from widgets.builtin import create_registry
from .bootstrap import initialize
from .main_window import MainWindow
from .diagnostics import install_exception_hooks
from .window_geometry import fit_startup_window


class ChineseParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, "启动参数无效，请使用 --help 查看说明。\n")


def main() -> int:
    if sys.argv[1:] == ["--preview-worker"]:
        from preview.worker import main as preview_main
        return preview_main()
    parser = ChineseParser(description="启动中文界面设计器。", add_help=False,
                           usage="python main.py [选项] 或 python -m app [选项]")
    parser._optionals.title = "可选参数"
    parser.add_argument("--help", action="help", help="显示启动说明")
    parser.add_argument("--smoke-test", action="store_true", help="运行启动检查并自动关闭测试窗口")
    parser.add_argument("--screenshot", type=Path, metavar="文件路径", help="启动检查时保存窗口截图")
    parser.add_argument("--release-check", type=Path, metavar="报告路径", help="检查保存、加载、导出和独立预览后退出")
    parser._positionals.title = "项目文件"
    parser.add_argument("projects", type=Path, nargs="*", metavar="项目路径", help="启动时打开一个或多个界面项目")
    options = parser.parse_args()
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    application = QApplication([sys.argv[0]])
    try:
        initialize(application)
        install_exception_hooks()
        registry = create_registry()
        verify_registry(registry)
        checking = options.smoke_test or bool(options.release_check)
        window = MainWindow(registry, enable_recovery=not checking, persist_settings=not checking)
        fit_startup_window(window, restored=window.geometry_restored)
        window.show()
        if options.projects:
            empty = window.document
            for path in options.projects:
                window._guard(lambda source=path: window.open_path(source))
            if window.tabs.count() > 1:
                window._close_document(empty)
        if options.release_check:
            from .release_check import ReleaseCheck
            window.release_check = ReleaseCheck(application, window, options.release_check)
            QTimer.singleShot(0, window.release_check.start)
        elif options.smoke_test:
            canvas = window.page.canvas
            button = canvas.create_component("builtin.button", QPointF(56, 56))
            label = canvas.create_component("builtin.label", QPointF(56, 128))
            document = window.document
            document.execute("测试按钮标题", lambda model: set_property(model, registry, button, "text", "确认"))
            document.execute("测试标签文本", lambda model: set_property(model, registry, label, "text", "拖动控件，编辑中文属性"))
            document.execute("测试标签宽度", lambda model: set_property(model, registry, label, "geometry.width", 280))
            document.select(button)

            def finish() -> None:
                code = 0
                try:
                    if options.screenshot:
                        options.screenshot.parent.mkdir(parents=True, exist_ok=True)
                        if not window.grab().save(str(options.screenshot)):
                            raise RuntimeError("启动检查截图保存失败。")
                    if sys.stdout:
                        print("启动检查通过：中文窗口、按钮、标签与属性面板已创建。")
                except Exception:
                    logging.getLogger(__name__).exception("启动检查失败。")
                    if sys.stderr:
                        print("启动检查失败，详细原因已写入诊断日志。", file=sys.stderr)
                    code = 1
                finally:
                    window.discard_all_for_test()
                    window.close()
                    application.exit(code)

            QTimer.singleShot(500, finish)
        return application.exec()
    except Exception as exc:
        logging.getLogger(__name__).exception("设计器启动失败。")
        message = str(exc) if isinstance(exc, DesignerError) else "设计器启动失败，请查看用户数据目录中的诊断日志。"
        if sys.stderr:
            print(message, file=sys.stderr)
        elif not (options.smoke_test or options.release_check):
            box = QMessageBox()
            box.setWindowTitle("启动失败")
            box.setText(message)
            box.addButton("关闭", QMessageBox.ButtonRole.AcceptRole)
            box.exec()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
