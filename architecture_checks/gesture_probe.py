"""验证手势快照的准备、合成和恢复；尚未接入完整画布状态机。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsView, QSizePolicy, QWidget

logger = logging.getLogger(__name__)


@dataclass
class GestureCapture:
    """被冻结的原生绘制层与独立的临时画面。"""

    view: QGraphicsView
    background: QImage
    previews: list[tuple[QRectF, QImage]]
    visibility: list[tuple[QWidget, bool, QSizePolicy]]
    updates_enabled: bool
    restored: bool = field(default=False, init=False)

    def paint(self, painter: QPainter, dx: float, dy: float) -> None:
        """在独立目标上合成，不修改真实控件的几何。"""
        painter.drawImage(QPoint(0, 0), self.background)
        for rectangle, preview in self.previews:
            target = QRectF(rectangle)
            target.translate(dx, dy)
            painter.drawImage(target, preview)

    def restore(self) -> None:
        """取消、结束和异常退出共用恢复动作，可重复调用。"""
        if self.restored:
            return
        try:
            for control, was_hidden, policy in self.visibility:
                control.setVisible(not was_hidden)
                control.setSizePolicy(policy)
        finally:
            self.view.setUpdatesEnabled(self.updates_enabled)
            self.restored = True


def capture_gesture(
    view: QGraphicsView, proxy: QGraphicsProxyWidget, controls: list[QWidget],
) -> GestureCapture:
    """只抓取最上层选中子树，失败时恢复已改变的显示状态。"""
    selected: list[QWidget] = []
    for control in controls:
        if control not in selected:
            selected.append(control)
    top_level = [control for control in selected
                 if not any(other is not control and other.isAncestorOf(control) for other in selected)]
    previous_updates = view.updatesEnabled()
    visibility: list[tuple[QWidget, bool, QSizePolicy]] = []
    previews: list[tuple[QRectF, QImage]] = []
    view.setUpdatesEnabled(False)
    try:
        for control in top_level:
            original_policy = QSizePolicy(control.sizePolicy())
            visibility.append((control, control.isHidden(), original_policy))
            if not control.isVisible():
                continue
            rectangle = view.viewportTransform().mapRect(proxy.mapRectToScene(proxy.subWidgetRect(control)))
            previews.append((rectangle, control.grab().toImage()))
            retained = QSizePolicy(original_policy)
            retained.setRetainSizeWhenHidden(True)
            control.setSizePolicy(retained)
            control.hide()
        # 准备期间不主动处理事件队列，避免关闭文档等操作重入。
        background = QImage(view.viewport().size(), QImage.Format.Format_ARGB32_Premultiplied)
        background.fill(Qt.GlobalColor.white)
        painter = QPainter(background)
        try:
            view.render(painter)
        finally:
            painter.end()
        return GestureCapture(view, background, previews, visibility, previous_updates)
    except Exception:
        logger.exception("手势快照准备失败，正在恢复真实控件显示。")
        for control, was_hidden, policy in visibility:
            control.setVisible(not was_hidden)
            control.setSizePolicy(policy)
        view.setUpdatesEnabled(previous_updates)
        raise
