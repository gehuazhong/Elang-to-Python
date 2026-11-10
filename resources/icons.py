"""加载软件图标，并使用 Qt 绘制统一线宽的界面图标。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from .colors import TEXT


def application_icon() -> QIcon:
    """从模块目录加载，兼容源码启动和 PyInstaller 便携包。"""
    return QIcon(str(Path(__file__).resolve().with_name("app_icon.ico")))


def ui_icon(name: str, color: str = TEXT) -> QIcon:
    name = {
        "dialog": "common_dialog", "message_box": "common_dialog", "error_message": "common_dialog",
        "input_dialog": "line_edit", "color_dialog": "drawing_board", "font_dialog": "font_combo_box",
        "progress_dialog": "progress_bar", "dialog_button_box": "tool_bar", "button_group": "radio_button",
        "list_view": "list_widget", "table_view": "table_widget", "tree_view": "tree_widget",
        "column_view": "super_list", "undo_view": "undo", "graphics_view": "drawing_board",
        "svg_widget": "picture_box", "splash_screen": "picture_box", "web_view": "text_browser",
        "stacked_widget": "tab_widget", "tool_box": "tab_widget", "tab_bar": "tab_widget",
        "wizard": "common_dialog", "wizard_page": "frame", "mdi_subwindow": "window",
    }.get(name, name)
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(2, 2)
        painter.setPen(QPen(QColor(color), 1.5, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if name in {"horizontal_layout", "vertical_layout", "grid_layout", "form_layout", "splitter"}:
            if name == "vertical_layout":
                painter.translate(24, 0)
                painter.rotate(90)
            if name in {"horizontal_layout", "vertical_layout", "splitter"}:
                for x in (3, 14):
                    painter.drawRect(QRectF(x, 4, 7, 16))
                if name == "splitter":
                    painter.drawLine(QPointF(12, 5), QPointF(12, 19))
            else:
                for y in (3, 14):
                    painter.drawRect(QRectF(3, y, 6 if name == "form_layout" else 7, 7))
                    painter.drawRect(QRectF(13, y, 8, 7))
        elif name == "spacer":
            painter.drawLine(QPointF(3, 12), QPointF(21, 12))
            for x, direction in ((3, 1), (21, -1)):
                painter.drawLine(QPointF(x, 12), QPointF(x + direction * 4, 8))
                painter.drawLine(QPointF(x, 12), QPointF(x + direction * 4, 16))
        elif name in {"dock_widget", "scroll_area", "mdi_area"}:
            painter.drawRect(QRectF(2, 3, 20, 18))
            if name == "dock_widget":
                painter.drawRect(QRectF(3, 4, 6, 16))
            elif name == "scroll_area":
                painter.drawLine(QPointF(18, 5), QPointF(18, 19))
                painter.drawRect(QRectF(17, 8, 2, 6))
            else:
                painter.drawRect(QRectF(5, 6, 10, 8))
                painter.drawRect(QRectF(10, 11, 9, 7))
        elif name in {"opengl_widget", "rhi_widget"}:
            painter.drawRect(QRectF(6, 6, 12, 12))
            for position in (8, 12, 16):
                painter.drawLine(QPointF(position, 3), QPointF(position, 6))
                painter.drawLine(QPointF(position, 18), QPointF(position, 21))
                painter.drawLine(QPointF(3, position), QPointF(6, position))
                painter.drawLine(QPointF(18, position), QPointF(21, position))
        elif name in {"window", "central", "button"}:
            painter.drawRoundedRect(QRectF(3, 5, 18, 14), 2, 2)
            if name == "window":
                painter.drawLine(QPointF(3, 9), QPointF(21, 9))
            elif name == "button":
                painter.drawLine(QPointF(8, 12), QPointF(16, 12))
        elif name == "label":
            painter.drawLine(QPointF(5, 5), QPointF(19, 5))
            painter.drawLine(QPointF(12, 5), QPointF(12, 19))
            painter.drawLine(QPointF(8, 19), QPointF(16, 19))
        elif name == "line_edit":
            painter.drawRect(QRectF(2, 6, 20, 12))
            painter.drawLine(QPointF(7, 9), QPointF(7, 15))
            painter.drawLine(QPointF(5, 9), QPointF(9, 9))
            painter.drawLine(QPointF(5, 15), QPointF(9, 15))
            painter.drawLine(QPointF(12, 12), QPointF(18, 12))
        elif name in {"text_edit", "rich_text_edit", "text_browser"}:
            painter.drawRect(QRectF(3, 3, 18, 18))
            for y, end in ((7, 17), (11, 17), (15, 13)):
                painter.drawLine(QPointF(6, y), QPointF(end, y))
            if name == "rich_text_edit":
                painter.drawLine(QPointF(6, 8), QPointF(17, 8))
            elif name == "text_browser":
                painter.drawLine(QPointF(16, 15), QPointF(19, 17))
                painter.drawLine(QPointF(19, 17), QPointF(16, 19))
        elif name == "font_combo_box":
            painter.drawRect(QRectF(2, 4, 20, 16))
            painter.drawLine(QPointF(5, 8), QPointF(13, 8))
            painter.drawLine(QPointF(9, 8), QPointF(9, 16))
            painter.drawLine(QPointF(16, 11), QPointF(18, 13))
            painter.drawLine(QPointF(18, 13), QPointF(20, 11))
        elif name == "key_sequence_edit":
            painter.drawRoundedRect(QRectF(2, 6, 20, 13), 2, 2)
            for x in (6, 10, 14, 18):
                painter.drawPoint(QPointF(x, 10))
            painter.drawLine(QPointF(7, 15), QPointF(17, 15))
        elif name in {"combo_box", "spin_box", "double_spin_box"}:
            painter.drawRect(QRectF(2, 6, 20, 12))
            painter.drawLine(QPointF(15, 6), QPointF(15, 18))
            painter.drawLine(QPointF(5, 12), QPointF(11, 12))
            painter.drawLine(QPointF(17, 12), QPointF(19, 14))
            painter.drawLine(QPointF(19, 14), QPointF(21, 12))
            if name in {"spin_box", "double_spin_box"}:
                painter.drawLine(QPointF(17, 10), QPointF(19, 8))
                painter.drawLine(QPointF(19, 8), QPointF(21, 10))
        elif name in {"check_box", "radio_button"}:
            if name == "check_box":
                painter.drawRect(QRectF(3, 6, 11, 11))
                painter.drawLine(QPointF(5, 11), QPointF(8, 14))
                painter.drawLine(QPointF(8, 14), QPointF(12, 9))
            else:
                painter.drawEllipse(QRectF(3, 6, 11, 11))
                painter.drawEllipse(QRectF(7, 10, 3, 3))
            painter.drawLine(QPointF(17, 11), QPointF(22, 11))
        elif name == "progress_bar":
            painter.drawRect(QRectF(2, 7, 20, 10))
            painter.fillRect(QRectF(5, 10, 10, 4), QColor(color))
        elif name == "slider":
            painter.drawLine(QPointF(2, 12), QPointF(22, 12))
            painter.drawRect(QRectF(8, 7, 5, 10))
        elif name in {"list_widget", "table_widget"}:
            painter.drawRect(QRectF(3, 3, 18, 18))
            for y in (8, 13, 18):
                painter.drawLine(QPointF(4, y), QPointF(20, y))
            painter.drawLine(QPointF(9 if name == "table_widget" else 6, 4), QPointF(9 if name == "table_widget" else 6, 20))
        elif name == "tree_widget":
            painter.drawLine(QPointF(5, 4), QPointF(5, 19))
            painter.drawLine(QPointF(5, 6), QPointF(11, 6))
            for y in (12, 18):
                painter.drawLine(QPointF(5, y), QPointF(13, y))
                painter.drawRect(QRectF(14, y - 2, 6, 4))
        elif name in {"group_box", "frame"}:
            painter.drawRect(QRectF(3, 5, 18, 16))
            if name == "group_box":
                painter.drawLine(QPointF(7, 3), QPointF(15, 3))
            painter.drawRect(QRectF(7, 10, 10, 6))
        elif name in {"date_edit", "datetime_edit", "calendar"}:
            painter.drawRect(QRectF(3, 5, 18, 16))
            painter.drawLine(QPointF(3, 10), QPointF(21, 10))
            for x in (7, 17):
                painter.drawLine(QPointF(x, 3), QPointF(x, 7))
            for x in (7, 12, 17):
                painter.drawPoint(QPointF(x, 14))
                painter.drawPoint(QPointF(x, 18))
        elif name in {"time_edit", "dial"}:
            painter.drawEllipse(QRectF(3, 3, 18, 18))
            painter.drawLine(QPointF(12, 12), QPointF(12, 6))
            painter.drawLine(QPointF(12, 12), QPointF(17, 15))
        elif name == "scroll_bar":
            painter.drawRect(QRectF(2, 8, 20, 8))
            painter.drawRect(QRectF(8, 9, 7, 6))
        elif name in {"tool_button", "command_link_button"}:
            painter.drawRect(QRectF(2, 4, 20, 16))
            painter.drawLine(QPointF(5, 12), QPointF(11, 12))
            painter.drawLine(QPointF(8, 9), QPointF(11, 12))
            painter.drawLine(QPointF(8, 15), QPointF(11, 12))
            painter.drawLine(QPointF(15, 9), QPointF(19, 9))
            if name == "command_link_button":
                painter.drawLine(QPointF(15, 15), QPointF(19, 15))
        elif name == "lcd_number":
            painter.drawRect(QRectF(2, 5, 20, 14))
            painter.drawRect(QRectF(5, 8, 5, 8))
            painter.drawLine(QPointF(13, 8), QPointF(18, 8))
            painter.drawLine(QPointF(18, 8), QPointF(18, 16))
        elif name in {"tab_widget", "tab_page"}:
            painter.drawRect(QRectF(3, 7, 18, 13))
            painter.drawRect(QRectF(3, 3, 7, 4))
            painter.drawRect(QRectF(11, 3, 7, 4))
        elif name in {"drawing_board", "picture_box"}:
            painter.drawRect(QRectF(3, 4, 18, 16))
            painter.drawEllipse(QRectF(6, 7, 3, 3))
            painter.drawLine(QPointF(4, 18), QPointF(11, 12))
            painter.drawLine(QPointF(11, 12), QPointF(20, 18))
        elif name == "timer":
            painter.drawEllipse(QRectF(3, 3, 18, 18))
            painter.drawLine(QPointF(12, 5), QPointF(12, 12))
            painter.drawLine(QPointF(12, 12), QPointF(17, 15))
        elif name in {"tool_bar", "status_bar"}:
            painter.drawRect(QRectF(2, 7, 20, 10))
            for x in (8, 15):
                painter.drawLine(QPointF(x, 9), QPointF(x, 15))
        elif name in {"super_list", "common_dialog"}:
            painter.drawRect(QRectF(2, 3, 20, 18))
            painter.drawLine(QPointF(2, 8), QPointF(22, 8))
            if name == "super_list":
                painter.drawLine(QPointF(9, 8), QPointF(9, 21))
                painter.drawLine(QPointF(2, 14), QPointF(22, 14))
            else:
                painter.drawRect(QRectF(12, 15, 7, 3))
        elif name == "new":
            painter.drawRoundedRect(QRectF(5, 3, 14, 18), 1.5, 1.5)
            painter.drawLine(QPointF(8, 12), QPointF(16, 12))
            painter.drawLine(QPointF(12, 8), QPointF(12, 16))
        elif name == "open":
            path = QPainterPath(QPointF(3, 7))
            for x, y in ((9, 7), (11, 9), (20, 9), (20, 19), (3, 19), (3, 7)):
                path.lineTo(x, y)
            painter.drawPath(path)
            painter.drawLine(QPointF(3, 12), QPointF(20, 12))
        elif name == "save":
            painter.drawRoundedRect(QRectF(4, 3, 16, 18), 1.5, 1.5)
            painter.drawRect(QRectF(8, 3, 8, 6))
            painter.drawRect(QRectF(8, 14, 8, 7))
        elif name in {"undo", "redo"}:
            if name == "redo":
                painter.translate(24, 0)
                painter.scale(-1, 1)
            path = QPainterPath(QPointF(5, 9))
            path.lineTo(14, 9)
            path.cubicTo(22, 9, 22, 19, 14, 19)
            painter.drawPath(path)
            painter.drawLine(QPointF(5, 9), QPointF(9, 5))
            painter.drawLine(QPointF(5, 9), QPointF(9, 13))
        elif name == "fit":
            for x, y, sx, sy in ((4, 4, 1, 1), (20, 4, -1, 1), (4, 20, 1, -1), (20, 20, -1, -1)):
                painter.drawLine(QPointF(x, y), QPointF(x + 5 * sx, y))
                painter.drawLine(QPointF(x, y), QPointF(x, y + 5 * sy))
        elif name == "preview":
            path = QPainterPath(QPointF(7, 4))
            path.lineTo(20, 12)
            path.lineTo(7, 20)
            path.closeSubpath()
            painter.setBrush(QColor(color))
            painter.drawPath(path)
        elif name == "stop":
            painter.drawRoundedRect(QRectF(5, 5, 14, 14), 1.5, 1.5)
        elif name == "search":
            painter.drawEllipse(QRectF(3, 3, 12, 12))
            painter.drawLine(QPointF(14, 14), QPointF(21, 21))
        elif name == "components":
            for x, y in ((3, 3), (13, 3), (3, 13), (13, 13)):
                painter.drawRect(QRectF(x, y, 7, 7))
        elif name == "settings":
            for y, x in ((5, 8), (12, 16), (19, 10)):
                painter.drawLine(QPointF(3, y), QPointF(21, y))
                painter.setBrush(QColor(color))
                painter.drawEllipse(QPointF(x, y), 2, 2)
        elif name == "output":
            painter.drawRect(QRectF(2, 4, 20, 16))
            painter.drawLine(QPointF(5, 8), QPointF(9, 12))
            painter.drawLine(QPointF(9, 12), QPointF(5, 16))
            painter.drawLine(QPointF(12, 16), QPointF(18, 16))
        elif name == "snap":
            path = QPainterPath(QPointF(5, 4))
            path.lineTo(5, 13)
            path.cubicTo(5, 22, 19, 22, 19, 13)
            path.lineTo(19, 4)
            painter.drawPath(path)
            painter.drawLine(QPointF(3, 8), QPointF(7, 8))
            painter.drawLine(QPointF(17, 8), QPointF(21, 8))
        elif name == "grid":
            for x in (5, 12, 19):
                for y in (5, 12, 19):
                    painter.drawPoint(QPointF(x, y))
        else:
            painter.drawRoundedRect(QRectF(5, 5, 14, 14), 2, 2)
    finally:
        painter.end()
    return QIcon(pixmap)
