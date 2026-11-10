"""每个标签页独立持有画布，会话状态不跨文档共享。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from core.document import ChangeSet, DocumentSession
from designer.canvas import DesignerCanvas


class CanvasPage(QWidget):
    window_properties_requested = Signal()

    def __init__(self, document: DocumentSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document = document
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QWidget()
        header.setObjectName("canvasHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(12, 3, 8, 3)
        self.title = QLabel()
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.title.setObjectName("canvasTitle")
        self.title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.info = QLabel()
        self.info.setObjectName("secondaryText")
        row.addWidget(self.title, 1)
        row.addWidget(self.info)
        self.window_button = QPushButton("窗口属性")
        self.window_button.setToolTip("选择主窗口，编辑标题、边框、窗口按钮与背景色。")
        self.window_button.clicked.connect(self.window_properties_requested)
        row.addWidget(self.window_button)
        layout.addWidget(header)
        self.canvas = DesignerCanvas(document)
        layout.addWidget(self.canvas)
        self._unsubscribe = document.subscribe(self.refresh)
        self.refresh()

    def refresh(self, change: ChangeSet | None = None) -> None:
        root = self.document.model.nodes[self.document.model.root_id]
        self.title.setText(root.properties.get("window_title", "窗口"))
        self.title.setToolTip(self.title.text())
        count = sum(node.slot in {"children", "tool_bar", "status_bar"} for node in self.document.model.nodes.values())
        non_visual = sum(node.slot == "non_visual" for node in self.document.model.nodes.values())
        self.info.setText(f"{root.geometry.width} × {root.geometry.height}　·　{count} 个可视控件" +
                         (f" · {non_visual} 个非可视组件" if non_visual else ""))

    def dispose(self) -> None:
        self._unsubscribe()
        self.canvas.dispose()

