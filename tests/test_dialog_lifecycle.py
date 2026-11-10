"""重复使用工作台对话框后，不应在主窗口中累积隐藏窗口。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from app.dialogs import ask_save, choose_project_file, choose_recovery
from app.main_window import MainWindow
from tests.test_clipboard import window


@pytest.mark.parametrize("kind", ["save", "recovery", "about", "project_open", "project_save"])
@pytest.mark.parametrize("failed", [False, True])
def test_dialog_releases_children_after_close_or_error(window: MainWindow, qt_app: QApplication,
                                                     monkeypatch: pytest.MonkeyPatch, kind: str, failed: bool) -> None:
    original = set(window.findChildren(QDialog))

    def execute(dialog: QDialog) -> int:
        if failed:
            raise RuntimeError("模拟对话框执行失败。")
        dialog.reject()
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", execute)
    monkeypatch.setattr(QMessageBox, "exec", execute)

    def invoke() -> object:
        if kind == "save":
            return ask_save(window, "待保存项目")
        if kind == "recovery":
            return choose_recovery(window, [])
        if kind in {"project_open", "project_save"}:
            return choose_project_file(window, Path.cwd() / "未保存项目.uipro" if kind == "project_save" else Path.cwd(),
                                       save=kind == "project_save")
        return window.show_about()

    if failed:
        with pytest.raises(RuntimeError, match="模拟"):
            invoke()
    else:
        result = invoke()
        assert result == ("cancel" if kind == "save" else None)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()
    assert set(window.findChildren(QDialog)) == original, "已关闭或失败的对话框仍由主窗口保留。"


@pytest.mark.parametrize("label, expected", [("保存", "save"), ("不保存", "discard"), ("取消", "cancel")])
def test_save_choice_is_read_before_dialog_disposal(window: MainWindow, qt_app: QApplication,
                                                 monkeypatch: pytest.MonkeyPatch, label: str, expected: str) -> None:
    def execute(dialog: QMessageBox) -> int:
        next(button for button in dialog.buttons() if button.text() == label).click()
        return dialog.result()

    monkeypatch.setattr(QMessageBox, "exec", execute)
    assert ask_save(window, "待保存项目") == expected
