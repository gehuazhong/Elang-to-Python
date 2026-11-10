"""中文图片选择器；导入时转换静态快照，项目不依赖原文件路径。"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, Qt, Signal
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from core.errors import DesignerError, require
from core.image_values import normalize_image
from runtime.application import configure_file_dialog

logger = logging.getLogger(__name__)


def import_image(path: Path, *, icon: bool = False) -> str:
    try:
        require(path.is_file() and path.stat().st_size <= 16 * 1024 * 1024, "图片源文件不能超过十六兆字节。")
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        if icon and bytes(reader.format()).lower() == b"ico" and reader.imageCount() > 1:
            # 多尺寸图标采用最清晰的一帧，再保存为不依赖源文件的静态快照。
            candidates: list[tuple[int, int]] = []
            for index in range(reader.imageCount()):
                if reader.jumpToImage(index):
                    size = reader.size()
                    if size.isValid():
                        candidates.append((size.width() * size.height(), index))
            require(bool(candidates) and reader.jumpToImage(max(candidates)[1]), "无法读取程序图标，请检查文件是否损坏。")
        size = reader.size()
        require(size.isValid() and 0 < size.width() <= 4096 and 0 < size.height() <= 4096
                and size.width() * size.height() <= 8_000_000, "图片尺寸过大或格式不支持。")
        picture = reader.read()
        require(not picture.isNull(), "无法读取图片，请检查文件是否损坏。")
        buffer = QBuffer()
        require(buffer.open(QIODevice.OpenModeFlag.WriteOnly), "无法准备图片快照。")
        require(picture.save(buffer, "PNG"), "图片转换失败。")
        value = base64.b64encode(bytes(buffer.data())).decode("ascii")
        return normalize_image(value)
    except OSError as exc:
        raise DesignerError("无法读取图片文件，请检查路径和权限。") from exc


class ImageEditor(QWidget):
    value_committed = Signal(str)
    error = Signal(str)
    editing_finished = Signal()

    def __init__(self, value: str, parent: QWidget | None = None, *, icon: bool = False) -> None:
        super().__init__(parent)
        self.choosing = False
        self.icon_mode = icon
        self.setAccessibleName("程序图标" if icon else "图片")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)
        if icon:
            preview = QLabel()
            preview.setFixedSize(20, 20)
            if value:
                pixmap = QPixmap()
                if pixmap.loadFromData(base64.b64decode(value), "PNG"):
                    ratio = self.devicePixelRatioF()
                    thumbnail = pixmap.scaled(round(20 * ratio), round(20 * ratio), Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
                    thumbnail.setDevicePixelRatio(ratio)
                    preview.setPixmap(thumbnail)
            row.addWidget(preview)
        label = QLabel(("已设置" if icon else "已嵌入图片") if value else "未设置")
        row.addWidget(label, 1)
        self.button = QPushButton("选择…")
        self.button.setAccessibleName("选择程序图标" if icon else "选择图片")
        self.button.clicked.connect(self.choose)
        row.addWidget(self.button)
        self.clear_button = QPushButton("清除")
        self.clear_button.setAccessibleName("清除程序图标" if icon else "清除图片")
        self.clear_button.setEnabled(bool(value))
        self.clear_button.clicked.connect(lambda: self.value_committed.emit(""))
        row.addWidget(self.clear_button)

    def choose(self) -> None:
        self.choosing = True
        dialog = QFileDialog(self, "选择程序图标" if self.icon_mode else "选择图片")
        configure_file_dialog(dialog)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("图标和图片 (*.ico *.png *.jpg *.jpeg *.bmp *.gif *.webp)" if self.icon_mode
                             else "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        dialog.setLabelText(QFileDialog.DialogLabel.Accept, "导入")
        dialog.setLabelText(QFileDialog.DialogLabel.Reject, "取消")
        try:
            if dialog.exec() == QFileDialog.DialogCode.Accepted and dialog.selectedFiles():
                self.value_committed.emit(import_image(Path(dialog.selectedFiles()[0]), icon=self.icon_mode))
        except DesignerError as exc:
            self.error.emit(str(exc))
        except Exception:
            logger.exception("图片导入失败。")
            self.error.emit("图片导入失败，详细原因已写入日志。")
        finally:
            self.choosing = False
            dialog.deleteLater()
            self.editing_finished.emit()
