"""VS Code Dark Modern inspired shell, isolated from designed windows."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QSize
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QGraphicsView, QMainWindow, QToolBar, QWidget

from resources.colors import COLORS


DESIGNER_QSS = """
QMainWindow { background: @background@; color: @text@; }
QMainWindow::separator { width: 4px; height: 4px; background: @border@; }
QMainWindow::separator:hover { background: @focus@; }
QDialog, QMessageBox { background: @sidebar@; color: @text@; }
QMenuBar { background: @title@; color: @text@; padding: 3px 8px; border-bottom: 1px solid @border@; }
QMenuBar::item { padding: 5px 10px; background: transparent; }
QMenuBar::item:selected { background: @hover@; border-radius: 3px; }
QMenu { background: @editor@; color: @text@; border: 1px solid @line_hover@; padding: 5px; }
QMenu::item { padding: 6px 28px 6px 24px; border-radius: 3px; }
QMenu::item:selected { background: @selected@; color: @white@; }
QMenu::item:disabled { color: @disabled@; }
QMenu::separator { height: 1px; background: @border@; margin: 5px 4px; }
QToolBar { background: @title@; border: 0; border-bottom: 1px solid @border@; padding: 4px 8px; spacing: 3px; }
QToolBar::separator { width: 1px; height: 1px; background: @border@; margin: 4px 6px; }
QToolBar#activityBar { background: @activity@; border-right: 1px solid @border@; padding: 4px 0; spacing: 4px; }
QToolBar#activityBar QToolButton { border: 0; border-left: 2px solid transparent; border-radius: 0; padding: 10px 3px; min-width: 22px; }
QToolBar#activityBar QToolButton:checked { border-left-color: @focus@; background: @hover@; }
QToolBar#activityBar QToolButton:focus { border-left-color: @white@; }
QDockWidget { background: @sidebar@; color: @text@; }
QDockWidget::title { background: @sidebar@; padding: 8px 10px; border-bottom: 1px solid @border@; }
QDockWidget::close-button, QDockWidget::float-button { border: 0; padding: 0; width: 16px; height: 16px; }
QDockWidget::close-button { image: url("@assets@/close.svg"); }
QDockWidget::float-button { image: url("@assets@/undock.svg"); }
QDockWidget::close-button:hover, QDockWidget::float-button:hover { background: @secondary@; }
QDockWidget > QWidget, QWidget#toolboxPanel, QWidget#propertyPanel { background: @sidebar@; }
QTabWidget::pane { border: 0; background: @editor@; }
QTabBar { background: @title@; }
QTabBar::tab { background: @title@; color: @muted@; border-right: 1px solid @border@; border-top: 2px solid transparent; padding: 8px 12px; }
QTabBar::tab:selected { background: @editor@; color: @white@; border-top-color: @focus@; }
QTabBar::tab:hover:!selected { background: @hover@; color: @text@; }
QTabBar::close-button { image: url("@assets@/close.svg"); width: 14px; height: 14px; }
QTabBar::close-button:hover { background: @secondary@; border-radius: 2px; }
QTreeView, QListView, QTableView { background: @sidebar@; alternate-background-color: @sidebar@; color: @text@; border: 0; outline: 0; selection-background-color: @selected@; selection-color: @white@; }
QTreeView::item, QListView::item { min-height: 24px; padding: 0 4px; }
QTreeWidget#componentTree::item { min-height: 28px; }
QTreeView::item:hover, QListView::item:hover { background: @hover@; }
QTreeView::item:selected, QListView::item:selected { background: @selected@; color: @white@; }
QTreeView::item:disabled, QListView::item:disabled { color: @disabled@; }
QTreeView::branch { background: transparent; }
QTreeView::branch:has-children:closed { image: url("@assets@/chevron_right.svg"); }
QTreeView::branch:has-children:open { image: url("@assets@/chevron_down.svg"); }
QHeaderView { background: @sidebar@; }
QHeaderView::section { background: @sidebar@; color: @muted@; border: 0; border-bottom: 1px solid @border@; padding: 5px 6px; }
QTableCornerButton::section, QAbstractScrollArea::corner { background: @sidebar@; border: 0; }
QTableView { gridline-color: @border@; }
QLineEdit, QAbstractSpinBox, QComboBox, QKeySequenceEdit { background: @input@; color: @text@; border: 1px solid @border@; border-radius: 2px; min-height: 22px; padding: 2px 6px; selection-background-color: @selected@; selection-color: @white@; }
QLineEdit:hover, QAbstractSpinBox:hover, QComboBox:hover, QKeySequenceEdit:hover { border-color: @line_hover@; }
QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus, QKeySequenceEdit:focus { border-color: @focus@; }
QLineEdit:disabled, QAbstractSpinBox:disabled, QComboBox:disabled, QKeySequenceEdit:disabled { color: @disabled@; background: @sidebar@; }
QComboBox { padding-right: 23px; }
QComboBox::drop-down { width: 22px; border: 0; }
QComboBox::down-arrow { image: url("@assets@/chevron_down.svg"); width: 12px; height: 12px; }
QComboBox QAbstractItemView { border: 1px solid @line_hover@; background: @editor@; selection-background-color: @selected@; selection-color: @white@; }
QAbstractSpinBox { padding-right: 19px; }
QAbstractSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 18px; border: 0; }
QAbstractSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 18px; border: 0; }
QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover { background: @secondary@; }
QAbstractSpinBox::up-arrow { image: url("@assets@/chevron_up.svg"); width: 12px; height: 12px; }
QAbstractSpinBox::down-arrow { image: url("@assets@/chevron_down.svg"); width: 12px; height: 12px; }
QPushButton { background: @secondary@; color: @text@; border: 1px solid transparent; border-radius: 2px; padding: 4px 10px; min-height: 20px; }
QToolButton { background: transparent; color: @text@; border: 1px solid transparent; border-radius: 3px; padding: 4px 6px; min-height: 20px; }
QPushButton:hover { background: @hover@; border-color: @line_hover@; }
QToolButton:hover { background: @hover@; }
QPushButton:pressed, QToolButton:pressed { background: @selected@; }
QPushButton:checked, QToolButton:checked { background: @selected@; color: @white@; }
QPushButton:focus, QToolButton:focus { border-color: @focus@; }
QPushButton:default, QPushButton#primaryButton { background: @button@; color: @white@; }
QPushButton:default:hover, QPushButton#primaryButton:hover { background: @button_hover@; }
QPushButton:disabled, QToolButton:disabled { color: @disabled@; background: transparent; }
QToolBar QToolButton { padding: 3px 7px; }
QToolBar QComboBox { min-height: 20px; }
QToolButton#commandButton { background: @input@; border: 1px solid @border@; margin-right: 6px; padding: 1px 14px; }
QToolButton#commandButton:hover { border-color: @line_hover@; }
QFileDialog QToolButton#backButton { qproperty-icon: url("@assets@/arrow_left.svg"); }
QFileDialog QToolButton#forwardButton { qproperty-icon: url("@assets@/arrow_right.svg"); }
QFileDialog QToolButton#toParentButton { qproperty-icon: url("@assets@/arrow_up.svg"); }
QLabel { background: transparent; color: @text@; }
QLabel#secondaryText { color: @muted@; }
QLabel#panelHeading { font-weight: 600; padding: 3px 0; }
QLabel#errorText { color: @error@; }
QWidget#canvasHeader { background: @editor@; border-bottom: 1px solid @border@; }
QWidget#canvasHeader QPushButton { background: transparent; padding: 2px 6px; }
QWidget#canvasHeader QPushButton:hover { background: @hover@; }
QWidget#welcomePage { background: @editor@; }
QLabel#welcomeTitle { font-size: 22pt; color: @text@; }
QPushButton#recoveryBanner { background: @selected@; color: @white@; text-align: left; padding: 8px 12px; }
QGroupBox { background: @sidebar@; color: @text@; border: 1px solid @border@; margin-top: 10px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QCheckBox, QRadioButton { color: @text@; spacing: 7px; }
QCheckBox:disabled, QRadioButton:disabled { color: @disabled@; }
QCheckBox::indicator, QGroupBox::indicator { width: 13px; height: 13px; border: 1px solid @line_hover@; border-radius: 2px; background: @input@; }
QCheckBox::indicator:checked, QGroupBox::indicator:checked { background: @button@; border-color: @focus@; image: url("@assets@/check.svg"); }
QCheckBox::indicator:indeterminate { image: url("@assets@/minus.svg"); }
QCheckBox::indicator:hover, QCheckBox::indicator:focus { border-color: @focus@; }
QCheckBox::indicator:disabled { background: @secondary@; border-color: @border@; }
QRadioButton::indicator { width: 13px; height: 13px; border: 1px solid @line_hover@; border-radius: 7px; background: @input@; }
QRadioButton::indicator:checked { background: @focus@; image: url("@assets@/radio_dot.svg"); }
QRadioButton::indicator:disabled { background: @secondary@; border-color: @border@; }
QTreeWidget#propertyTree::item { border-bottom: 1px solid @border@; }
QTreeWidget#propertyTree QLineEdit, QTreeWidget#propertyTree QAbstractSpinBox, QTreeWidget#propertyTree QComboBox { background: @editor@; border: 1px solid transparent; border-radius: 0; min-height: 22px; padding-top: 1px; padding-bottom: 1px; }
QTreeWidget#propertyTree QLineEdit:hover, QTreeWidget#propertyTree QAbstractSpinBox:hover, QTreeWidget#propertyTree QComboBox:hover { background: @input@; }
QTreeWidget#propertyTree QLineEdit:focus, QTreeWidget#propertyTree QAbstractSpinBox:focus, QTreeWidget#propertyTree QComboBox:focus { background: @input@; border-color: @focus@; }
QTreeWidget#propertyTree QLineEdit:disabled, QTreeWidget#propertyTree QAbstractSpinBox:disabled, QTreeWidget#propertyTree QComboBox:disabled { color: @disabled@; background: @sidebar@; }
QAbstractSpinBox QLineEdit, QTreeWidget#propertyTree QAbstractSpinBox QLineEdit, QKeySequenceEdit QLineEdit { border: 0; background: transparent; padding: 0; min-height: 0; }
QTreeWidget#propertyTree QPushButton { padding: 2px 5px; background: transparent; }
QTreeWidget#propertyTree QPushButton:hover { background: @hover@; }
QPlainTextEdit, QTextEdit, QTextBrowser { background: @editor@; color: @text@; border: 1px solid @border@; selection-background-color: @selected@; selection-color: @white@; }
QPlainTextEdit#outputPanel { border: 0; padding: 5px 10px; }
QSplitter::handle { background: @border@; width: 3px; height: 3px; }
QSplitter::handle:hover { background: @focus@; }
QGraphicsView { background: @background@; border: 0; }
QStatusBar { background: @status@; color: @white@; border: 0; min-height: 23px; }
QStatusBar::item { border: 0; }
QStatusBar QLabel { color: @white@; padding: 0 8px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:vertical { background: @secondary@; min-height: 28px; }
QScrollBar::handle:horizontal { background: @secondary@; min-width: 28px; }
QScrollBar::handle:hover { background: @line_hover@; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QProgressBar { background: @input@; color: @white@; border: 1px solid @border@; text-align: center; }
QProgressBar::chunk { background: @focus@; }
QSlider::groove:horizontal { height: 3px; background: @secondary@; }
QSlider::handle:horizontal { width: 12px; margin: -5px 0; background: @focus@; border-radius: 2px; }
QCalendarWidget QWidget { alternate-background-color: @sidebar@; }
QCalendarWidget QAbstractItemView { background: @editor@; color: @text@; selection-background-color: @selected@; }
QDialog#commandPalette { border: 1px solid @line_hover@; background: @editor@; }
QTreeWidget#commandResults { background: @editor@; }
QTreeWidget#commandResults::item { min-height: 32px; padding: 0 8px; }
QToolTip { background: @editor@; color: @text@; border: 1px solid @line_hover@; padding: 5px 8px; }
"""

for _key, _value in {**COLORS, "assets": (Path(__file__).resolve().parent.parent / "resources").as_posix()}.items():
    DESIGNER_QSS = DESIGNER_QSS.replace(f"@{_key}@", _value)


def designer_palette(base: QPalette | None = None) -> QPalette:
    palette = QPalette(base) if base is not None else QPalette()
    for role, token in {
        "Window": "background", "WindowText": "text", "Base": "editor",
        "AlternateBase": "sidebar", "ToolTipBase": "editor", "ToolTipText": "text",
        "Text": "text", "Button": "secondary", "ButtonText": "text",
        "BrightText": "white", "Highlight": "selected", "HighlightedText": "white",
        "Link": "link", "PlaceholderText": "muted", "Light": "line_hover",
        "Midlight": "secondary", "Mid": "border", "Dark": "sidebar", "Shadow": "title",
    }.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(COLORS[token]))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(COLORS["disabled"]))
    return palette


def apply_designer_theme(window: QWidget) -> None:
    if window.property("uiplay_vscode_theme"):
        return
    window.setProperty("uiplay_vscode_theme", True)
    window.setPalette(designer_palette(window.palette()))
    window.setFont(QFont("Microsoft YaHei UI", 9))
    for toolbar in window.findChildren(QToolBar):
        toolbar.setIconSize(QSize(22, 22) if toolbar.objectName() == "activityBar" else QSize(16, 16))
    for view in window.findChildren(QGraphicsView):
        view.setBackgroundBrush(QColor(COLORS["background"]))
    window.setStyleSheet(DESIGNER_QSS)


class DesignerThemeFilter(QObject):
    """Compatibility for hosts that instantiate the designer through bootstrap."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (event.type() in {QEvent.Type.Polish, QEvent.Type.Show}
                and isinstance(watched, QMainWindow)
                and type(watched).__module__ == "app.main_window"):
            apply_designer_theme(watched)
        return False


def install_designer_theme(application: QApplication) -> None:
    if getattr(application, "_uiplay_designer_theme_filter", None) is None:
        event_filter = DesignerThemeFilter(application)
        application.installEventFilter(event_filter)
        application._uiplay_designer_theme_filter = event_filter
