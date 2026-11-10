"""所有自主定义的对话框按钮与提示使用中文。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget

from core.errors import DesignerError
from core.storage import load_project


# Qt 用半角括号提取通配符，全角括号会成为文件名匹配条件。
PROJECT_FILE_FILTER = "界面项目 (*.uipro)"


def settings_directory(settings, key: str) -> Path:
    value = settings.value(key, "")
    if isinstance(value, str) and value.strip() and "\x00" not in value:
        try:
            directory = Path(value).expanduser()
            if directory.is_dir():
                return directory.resolve()
        except (OSError, ValueError, RuntimeError):
            pass
    return Path.home()


def choose_project_file(parent: QWidget, initial: Path, *, save: bool = False) -> str | None:
    # 先完成对话框状态恢复，再设置本次筛选和目录，避免构造参数与恢复目录交错。
    dialog = QFileDialog(parent)
    try:
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setWindowTitle("保存界面项目" if save else "打开界面项目")
        dialog.setFileMode(QFileDialog.FileMode.AnyFile if save else QFileDialog.FileMode.ExistingFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave if save else QFileDialog.AcceptMode.AcceptOpen)
        dialog.setNameFilters([PROJECT_FILE_FILTER] if save else [PROJECT_FILE_FILTER, "所有文件 (*)"])
        dialog.selectNameFilter(PROJECT_FILE_FILTER)
        dialog.setLabelText(QFileDialog.DialogLabel.Accept, "保存" if save else "打开")
        dialog.setLabelText(QFileDialog.DialogLabel.Reject, "取消")
        if save:
            dialog.setDirectory(str(initial.parent))
            dialog.selectFile(initial.name)
            dialog.setDefaultSuffix("uipro")
        else:
            dialog.setDirectory(str(initial))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.selectedFiles()
            return selected[0] if selected else None
        return None
    finally:
        dialog.deleteLater()


def ask_save(parent: QWidget, name: str) -> str:
    box = QMessageBox(parent)
    try:
        box.setWindowTitle("保存修改")
        box.setText(f"“{name}”有尚未保存的修改。")
        box.setInformativeText("关闭前是否保存？")
        save = box.addButton("保存", QMessageBox.ButtonRole.AcceptRole)
        discard = box.addButton("不保存", QMessageBox.ButtonRole.DestructiveRole)
        cancel = box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(save)
        box.setEscapeButton(cancel)
        box.exec()
        return "save" if box.clickedButton() is save else "discard" if box.clickedButton() is discard else "cancel"
    finally:
        box.deleteLater()


def choose_recovery(parent: QWidget, paths: list[Path]) -> Path | None:
    dialog = QDialog(parent)
    try:
        dialog.setWindowTitle("恢复未保存的项目")
        dialog.resize(640, 380)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("恢复内容将打开为未保存副本，不覆盖来源项目。"))
        listing = QListWidget()
        layout.addWidget(listing)
        for path in paths:
            try:
                loaded = load_project(path)
                timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y年%m月%d日 %H:%M:%S")
                item = QListWidgetItem(f"{loaded.model.name}　·　{timestamp}")
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                listing.addItem(item)
            except (DesignerError, OSError):
                continue
        buttons = QHBoxLayout()
        buttons.addStretch()
        restore, cancel = QPushButton("恢复选中项目"), QPushButton("暂不恢复")
        buttons.addWidget(restore)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        restore.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        listing.itemDoubleClicked.connect(lambda item: dialog.accept())
        if listing.count():
            listing.setCurrentRow(0)
        restore.setEnabled(listing.count() > 0)
        if dialog.exec() == QDialog.DialogCode.Accepted and listing.currentItem():
            return Path(listing.currentItem().data(Qt.ItemDataRole.UserRole))
        return None
    finally:
        dialog.deleteLater()
