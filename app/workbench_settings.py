"""工作台偏好和布局快照；与项目模型、预览窗口保持独立。"""

from dataclasses import asdict, dataclass, replace
import json

from PySide6.QtCore import QByteArray, QSettings, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDockWidget, QTabWidget

from .designer_theme import DESIGNER_QSS


SETTINGS_KEY = "workbench/preferences_v1"
LAYOUTS = (("standard", "标准布局"), ("compact", "紧凑侧栏"), ("right", "右侧组件箱"), ("focus", "专注画布"))
AREAS = {"left": Qt.DockWidgetArea.LeftDockWidgetArea, "right": Qt.DockWidgetArea.RightDockWidgetArea,
         "bottom": Qt.DockWidgetArea.BottomDockWidgetArea, "top": Qt.DockWidgetArea.TopDockWidgetArea}


@dataclass(frozen=True)
class WorkbenchPreferences:
    font_family: str = "Microsoft YaHei UI"
    font_size: int = 9
    density: str = "standard"
    toolbar_icon_size: int = 16
    document_tabs: str = "top"
    lock_panels: bool = False
    main_toolbar_visible: bool = True
    activity_bar_visible: bool = True
    status_bar_visible: bool = True


def load_preferences(settings):
    defaults = WorkbenchPreferences()
    try:
        data = json.loads(settings.value(SETTINGS_KEY, "{}"))
    except (ValueError, TypeError):
        return defaults
    if not isinstance(data, dict):
        return defaults
    valid = {}
    for key, default in asdict(defaults).items():
        value = data.get(key, default)
        if type(value) is not type(default):
            continue
        if key == "font_family" and (not value.strip() or len(value) > 200):
            continue
        if key == "font_size" and not 8 <= value <= 20:
            continue
        if key == "toolbar_icon_size" and value not in (16, 20, 24, 28, 32):
            continue
        if key == "density" and value not in ("compact", "standard", "comfortable"):
            continue
        if key == "document_tabs" and value not in ("top", "bottom"):
            continue
        valid[key] = value
    return replace(defaults, **valid)


def docks(window):
    return {"toolbox": window.toolbox_dock, "objects": window.object_dock,
            "properties": window.property_dock, "output": window.output_dock}


def current_preferences(window):
    return replace(window.workbench_preferences, main_toolbar_visible=not window.main_toolbar.isHidden(),
                   activity_bar_visible=not window.activity_bar.isHidden(),
                   status_bar_visible=not window.statusBar().isHidden())


def font_declaration(family, size):
    escaped = family.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    return f'font-family: "{escaped}"; font-size: {size}pt;'


def apply_preferences(window, preferences):
    previous_size = getattr(window, "_applied_workbench_font_size", 9)
    window._applied_workbench_font_size = preferences.font_size
    window.workbench_preferences = preferences
    window.setFont(QFont(preferences.font_family, preferences.font_size))
    # Qt's stylesheet font cache does not reliably follow a parent setFont().
    style = DESIGNER_QSS + "\nQWidget { " + font_declaration(preferences.font_family, preferences.font_size) + " }\n"
    if preferences.density != "standard":
        padding, height = (4, 20) if preferences.density == "compact" else (10, 32)
        style += f"""
QMenuBar::item {{ padding: {padding}px 10px; }}
QTabBar::tab {{ padding: {padding}px 12px; }}
QTreeView::item, QListView::item, QTreeWidget#componentTree::item {{ min-height: {height}px; }}
QDockWidget::title {{ padding: {padding}px 10px; }}
"""
    if window.styleSheet() != style:
        window.setStyleSheet(style)
    scale = preferences.font_size / 9
    window.toolbox.setMinimumWidth(max(182, round(182 * scale)))
    window.properties.setMinimumWidth(max(280, round(280 * scale)))
    if previous_size != preferences.font_size:
        window.properties.tree.setColumnWidth(0, round(window.properties.tree.columnWidth(0) * preferences.font_size / previous_size))
    window.main_toolbar.setIconSize(QSize(preferences.toolbar_icon_size, preferences.toolbar_icon_size))
    window.main_toolbar.setVisible(preferences.main_toolbar_visible)
    window.activity_bar.setVisible(preferences.activity_bar_visible)
    window.statusBar().setVisible(preferences.status_bar_visible)
    window.tabs.setTabPosition(QTabWidget.TabPosition.North if preferences.document_tabs == "top" else QTabWidget.TabPosition.South)
    features = QDockWidget.DockWidgetFeature.DockWidgetClosable
    if not preferences.lock_panels:
        features |= QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable
    for dock in docks(window).values():
        if preferences.lock_panels and dock.isFloating():
            dock.setFloating(False)
        dock.setFeatures(features)
    row_height = {"compact": 24, "standard": 28, "comfortable": 34}[preferences.density]
    window.toolbox.setProperty("workbench_row_height", row_height)
    window.properties.setProperty("workbench_row_height", row_height)
    window.toolbox.sync_font_metrics()
    window.properties.sync_font_metrics()


@dataclass(frozen=True)
class WorkbenchSnapshot:
    preferences: WorkbenchPreferences
    state: QByteArray
    geometry: QByteArray
    property_column_width: int


def capture_workbench(window):
    return WorkbenchSnapshot(current_preferences(window), window.saveState(), window.saveGeometry(), window.properties.tree.columnWidth(0))


def restore_workbench(window, snapshot):
    apply_preferences(window, snapshot.preferences)
    window.restoreState(snapshot.state)
    window.restoreGeometry(snapshot.geometry)
    window.properties.tree.setColumnWidth(0, snapshot.property_column_width)


def apply_layout_preset(window, preset):
    if preset not in dict(LAYOUTS):
        raise ValueError("未知工作台布局")
    preferences = current_preferences(window)
    window.restoreState(window._default_layout)
    if preset == "compact":
        window.tabifyDockWidget(window.toolbox_dock, window.object_dock)
        window.toolbox_dock.raise_()
        window.output_dock.hide()
    elif preset == "right":
        window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, window.property_dock)
        window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.toolbox_dock)
        window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.object_dock)
        window.splitDockWidget(window.toolbox_dock, window.object_dock, Qt.Orientation.Vertical)
    elif preset == "focus":
        for dock in docks(window).values():
            dock.hide()
    apply_preferences(window, preferences)


def save_workbench(window):
    if not window.persist_settings:
        return True
    settings = window.settings
    values = {SETTINGS_KEY: json.dumps(asdict(current_preferences(window)), ensure_ascii=False),
              "window/state_v2": window.saveState(),
              "workbench/property_column_width": window.properties.tree.columnWidth(0)}
    previous = {key: settings.value(key) for key in values}
    for key, value in values.items():
        settings.setValue(key, value)
    settings.sync()
    if settings.status() == QSettings.Status.NoError:
        return True
    for key, value in previous.items():
        settings.remove(key) if value is None else settings.setValue(key, value)
    settings.sync()
    return False
