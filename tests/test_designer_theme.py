"""The VS Code inspired shell theme must not leak into user-designed windows."""

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QGraphicsView, QMainWindow, QToolBar

from app.designer_theme import COLORS, DESIGNER_QSS, DesignerThemeFilter, apply_designer_theme
from core.document import DocumentSession
from panels.properties import PropertyPanel
from runtime.builder import RuntimeTree
from preview.protocol import preview_plan
from resources.icons import ui_icon


def test_designer_theme_install_is_idempotent(qt_app):
    window = QMainWindow()
    toolbar = QToolBar(window)
    view = QGraphicsView(window)
    window.addToolBar(toolbar)
    window.setCentralWidget(view)
    try:
        apply_designer_theme(window)
        first = window.styleSheet()
        apply_designer_theme(window)
        assert window.styleSheet() == first == DESIGNER_QSS
        assert window.palette().color(QPalette.ColorRole.Window).name() == COLORS["background"]
        assert toolbar.iconSize() == QSize(16, 16)
        assert view.backgroundBrush().color().name() == COLORS["background"]
    finally:
        window.deleteLater()


def test_default_ui_icons_are_visible_on_dark_shell(qt_app):
    pixmap = ui_icon("button").pixmap(24, 24)
    image = pixmap.toImage()
    visible = [image.pixelColor(x, y) for y in range(image.height()) for x in range(image.width())
               if image.pixelColor(x, y).alpha() > 0]
    assert visible
    assert max(color.lightness() for color in visible) >= 150


def test_property_groups_do_not_keep_light_item_backgrounds(project, registry, qt_app):
    document = DocumentSession(project, registry)
    document.select(project.root_id)
    panel = PropertyPanel()
    try:
        panel.bind(document)
        apply_designer_theme(panel)
        qt_app.processEvents()
        groups = [panel.tree.topLevelItem(index) for index in range(panel.tree.topLevelItemCount())]
        assert groups
        assert all(item.background(0).style() == Qt.BrushStyle.NoBrush for item in groups)
        assert all(item.sizeHint(0).height() >= 24 for item in groups)
        editor_rows = []
        for group in groups:
            for index in range(group.childCount()):
                item = group.child(index)
                for column in (0, 1):
                    editor = panel.tree.itemWidget(item, column)
                    if editor is not None:
                        editor_rows.append((item, column, editor))
        assert editor_rows
        assert all(item.sizeHint(column).height() >= editor.sizeHint().height()
                   for item, column, editor in editor_rows)
    finally:
        panel.bind(None)
        panel.deleteLater()


def test_theme_filter_ignores_runtime_windows(qt_app):
    event_filter = DesignerThemeFilter(qt_app)
    runtime = QMainWindow()
    qt_app.installEventFilter(event_filter)
    try:
        runtime.show()
        qt_app.processEvents()
        assert not runtime.property("uiplay_vscode_theme")
    finally:
        qt_app.removeEventFilter(event_filter)
        runtime.close()
        runtime.deleteLater()
        event_filter.deleteLater()


def test_theme_filter_targets_designer_window(qt_app):
    event_filter = DesignerThemeFilter(qt_app)
    designer_type = type("ThemeTestDesigner", (QMainWindow,), {"__module__": "app.main_window"})
    designer = designer_type()
    qt_app.installEventFilter(event_filter)
    try:
        designer.show()
        qt_app.processEvents()
        assert designer.property("uiplay_vscode_theme")
        assert designer.styleSheet() == DESIGNER_QSS
    finally:
        qt_app.removeEventFilter(event_filter)
        designer.close()
        designer.deleteLater()
        event_filter.deleteLater()


def test_theme_does_not_change_designed_window_palette(project, registry, qt_app):
    theme_filter = DesignerThemeFilter(qt_app)
    qt_app.installEventFilter(theme_filter)
    tree = RuntimeTree(registry)
    try:
        tree.apply(preview_plan(project, registry, "theme isolation"))
        assert not tree.root.property("uiplay_vscode_theme")
        assert tree.root.palette().color(QPalette.ColorRole.Base).name() != COLORS["background"]
    finally:
        qt_app.removeEventFilter(theme_filter)
        tree.dispose()
        theme_filter.deleteLater()
