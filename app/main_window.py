"""组装中文菜单、多文档画布和面板；所有编辑路由到当前文档。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QByteArray, QSettings, QSize, QStandardPaths, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QDockWidget, QFileDialog,
    QLabel, QMainWindow, QMessageBox, QPushButton, QStyle,
    QSizePolicy, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from core.build_plan import compile_plan
from core.document import DocumentSession
from core.deferred import defer
from core.errors import DesignerError, require
from core.models import new_project
from core.recovery import RecoveryService
from core.registry import WidgetRegistry
from core.save_service import SaveService
from core.storage import FileLease, load_project, path_key
from codegen.publisher import export_project
from panels.object_tree import ObjectTree
from panels.output import OutputPanel
from panels.properties import PropertyPanel
from panels.toolbox import ToolboxPanel
from panels.support_dialog import SupportDialog
from panels.menu_editor import MenuEditor
from resources.icons import application_icon, ui_icon
from resources.colors import ACCENT
from preview.service import PreviewService
from .dialogs import ask_save, choose_project_file, choose_recovery, settings_directory
from .edit_actions import EditActions
from .workspace import CanvasPage
from .designer_theme import apply_designer_theme
from .command_palette import CommandPalette
from .diagnostics import export_diagnostics
from .version import CHANNEL, VERSION
from .workbench_settings import (WorkbenchPreferences, apply_layout_preset, apply_preferences,
                                 load_preferences, save_workbench, LAYOUTS)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, registry: WidgetRegistry, *, settings: QSettings | None = None,
                 recovery_directory: Path | None = None, enable_recovery: bool = True,
                 persist_settings: bool = True) -> None:
        super().__init__()
        self.registry = registry
        self.settings = settings or QSettings()
        self.persist_settings = persist_settings
        self.workbench_preferences = load_preferences(self.settings) if persist_settings else WorkbenchPreferences()
        self._recent_paths: list[str] = []
        stored = self.settings.value("files/recent", []) if persist_settings else []
        if isinstance(stored, list):
            self._recent_paths = [item for item in stored if isinstance(item, str) and item][:10]
        self._closed = False
        self._exit_requested = False
        self._pending_close: set[str] = set()
        self._recovery_sources: dict[str, Path] = {}
        self._new_number = 0
        self._switching = False
        self.setWindowTitle("中文界面设计器")
        self.resize(1280, 820)
        self.setMinimumSize(960, 620)
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)
        apply_designer_theme(self)
        self.setWindowIcon(application_icon())
        central = QWidget()
        center_layout = QVBoxLayout(central)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        self.recovery_button = QPushButton()
        self.recovery_button.setObjectName("recoveryBanner")
        self.recovery_button.hide()
        self.recovery_button.clicked.connect(self.show_recovery)
        center_layout.addWidget(self.recovery_button)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("documentTabs")
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabBar().setUsesScrollButtons(True)
        center_layout.addWidget(self.tabs)
        self.welcome = QWidget()
        self.welcome.setObjectName("welcomePage")
        welcome_layout = QVBoxLayout(self.welcome)
        welcome_layout.setContentsMargins(24, 24, 24, 24)
        welcome_layout.setSpacing(14)
        welcome_layout.addStretch()
        title = QLabel("中文界面设计器")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(title)
        subtitle = QLabel("从一个窗口，开始设计。")
        subtitle.setObjectName("secondaryText")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(subtitle)
        for text, callback in (("新建项目    Ctrl+N", self.new_document),
                               ("打开项目    Ctrl+O", self.open_dialog),
                               ("搜索命令    Ctrl+Shift+P", self.show_commands)):
            button = QPushButton(text)
            button.setMinimumWidth(240)
            button.clicked.connect(lambda checked=False, run=callback: self._guard(run))
            welcome_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        welcome_layout.addStretch()
        self.welcome.hide()
        center_layout.addWidget(self.welcome)
        self.setCentralWidget(central)
        self.toolbox = ToolboxPanel(registry)
        self.properties = PropertyPanel()
        self.object_tree = ObjectTree()
        self.object_tree.before_selection = self.properties.commit_pending
        self.output = OutputPanel()
        self.toolbox_dock = self._dock("组件箱", "toolbox", self.toolbox, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.property_dock = self._dock("属性", "properties", self.properties, Qt.DockWidgetArea.RightDockWidgetArea)
        self.object_dock = self._dock("对象树", "objects", self.object_tree, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.output_dock = self._dock("输出", "output", self.output, Qt.DockWidgetArea.BottomDockWidgetArea)
        self.splitDockWidget(self.toolbox_dock, self.object_dock, Qt.Orientation.Vertical)
        self.resizeDocks([self.toolbox_dock, self.property_dock], [216, 320], Qt.Orientation.Horizontal)
        self.resizeDocks([self.toolbox_dock, self.object_dock], [300, 240], Qt.Orientation.Vertical)
        self.resizeDocks([self.output_dock], [72], Qt.Orientation.Vertical)
        self.save_service = SaveService(self)
        self.save_service.finished.connect(self._saved)
        self.recovery: RecoveryService | None = None
        if enable_recovery:
            directory = recovery_directory or Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "恢复副本"
            try:
                self.recovery = RecoveryService(directory, self)
                self.recovery.notice.connect(self.report_error)
            except OSError:
                logger.exception("恢复目录无法建立。")
                self.report_error("恢复目录无法建立，自动恢复暂不可用；仍可手动保存。")
        self.actions: dict[str, QAction] = {}
        self.preview_service = PreviewService(registry, self)
        self.preview_service.notice.connect(self._preview_notice)
        self.preview_service.error.connect(self.report_error)
        self.preview_service.changed.connect(self._refresh_actions)
        self._build_actions()
        self._build_activity_bar()
        self.document_status = QLabel()
        self.document_status.setAccessibleName("文档保存状态")
        self.preview_status = QLabel()
        self.preview_status.setAccessibleName("预览状态")
        self.statusBar().addPermanentWidget(self.document_status)
        self.statusBar().addPermanentWidget(self.preview_status)
        self._default_layout = self.saveState()
        apply_preferences(self, self.workbench_preferences)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.tabs.tabCloseRequested.connect(self.request_close)
        self.toolbox.create_requested.connect(self._create_component)
        self.properties.error.connect(self.report_error)
        self.properties.menu_edit_requested.connect(self.edit_menus)
        self.object_tree.itemDoubleClicked.connect(self._object_double_clicked)
        self.statusBar().showMessage("从组件箱拖入控件；拖到容器内部可创建子控件。")
        self.geometry_restored = False
        self.layout_restored = False
        if self.persist_settings:
            geometry = self.settings.value("window/geometry")
            state = self.settings.value("window/state_v2")
            if isinstance(geometry, (QByteArray, bytes, bytearray)):
                self.geometry_restored = self.restoreGeometry(geometry)
            if isinstance(state, (QByteArray, bytes, bytearray)):
                self.layout_restored = self.restoreState(state)
            width = self.settings.value("workbench/property_column_width")
            if type(width) is int and 44 <= width <= 800:
                self.properties.tree.setColumnWidth(0, width)
        self.new_document()
        self.refresh_recovery_notice()

    def _dock(self, title: str, name: str, content: QWidget, area: Qt.DockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setObjectName(name)
        dock.setWidget(content)
        self.addDockWidget(area, dock)
        return dock

    def _action(self, key: str, title: str, callback: Callable[[], object], shortcut: str = "",
                icon: QStyle.StandardPixmap | None = None) -> QAction:
        action = QAction(title, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setToolTip(f"{title}（{shortcut}）")
        action.setStatusTip(action.toolTip())
        if icon is not None:
            action.setIcon(self.style().standardIcon(icon))
        action.triggered.connect(lambda checked=False: self._guard(callback))
        self.actions[key] = action
        return action

    def _build_actions(self) -> None:
        file_menu = self.menuBar().addMenu("文件")
        toolbar = QToolBar("常用操作", self)
        self.main_toolbar = toolbar
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        for key, title, callback, shortcut, icon in (
            ("new", "新建", self.new_document, "Ctrl+N", QStyle.StandardPixmap.SP_FileIcon),
            ("open", "打开", self.open_dialog, "Ctrl+O", QStyle.StandardPixmap.SP_DialogOpenButton),
            ("save", "保存", self.save_current, "Ctrl+S", QStyle.StandardPixmap.SP_DialogSaveButton),
        ):
            action = self._action(key, title, callback, shortcut, icon)
            action.setIcon(ui_icon(key))
            file_menu.addAction(action)
            toolbar.addAction(action)
        file_menu.addAction(self._action("save_as", "另存为", lambda: self.save_current(force_as=True), "Ctrl+Shift+S"))
        self.recent_menu = file_menu.addMenu("最近项目")
        self._refresh_recent_menu()
        file_menu.addSeparator()
        file_menu.addAction(self._action("export_python", "导出 Python 项目…", self.export_python_dialog, "Ctrl+Shift+E"))
        file_menu.addSeparator()
        file_menu.addAction(self._action("close", "关闭项目", lambda: self.request_close(self.tabs.currentIndex()), "Ctrl+W"))
        file_menu.addAction(self._action("exit", "退出", self.close, "Ctrl+Q"))
        edit_menu = self.menuBar().addMenu("编辑")
        toolbar.addSeparator()
        for key, title, callback, shortcut, icon in (
            ("undo", "撤销", self.undo, "Ctrl+Z", QStyle.StandardPixmap.SP_ArrowBack),
            ("redo", "重做", self.redo, "Ctrl+Y", QStyle.StandardPixmap.SP_ArrowForward),
        ):
            action = self._action(key, title, callback, shortcut, icon)
            action.setIcon(ui_icon(key))
            edit_menu.addAction(action)
            toolbar.addAction(action)
            toolbar.widgetForAction(action).setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.edit_actions = EditActions(self, edit_menu)
        run_menu = self.menuBar().addMenu("运行")
        toolbar.addSeparator()
        preview_action = self._action("preview", "预览", self.preview_current, "F5")
        preview_action.setIcon(ui_icon("preview", ACCENT))
        preview_action.setToolTip("预览当前界面（F5），无需保存；再次预览会更新内容。")
        stop_action = self._action("stop_preview", "停止预览", self.preview_service.stop, "Shift+F5")
        stop_action.setIcon(ui_icon("stop"))
        for action in (preview_action, stop_action):
            run_menu.addAction(action)
            toolbar.addAction(action)
        toolbar.widgetForAction(stop_action).setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        view_menu = self.menuBar().addMenu("视图")
        command_action = self._action("commands", "搜索命令…", self.show_commands, "Ctrl+Shift+P")
        command_action.setObjectName("commandPaletteAction")
        command_action.setIcon(ui_icon("search"))
        view_menu.addAction(command_action)
        view_menu.addSeparator()
        command_button = QToolButton(self)
        command_button.setObjectName("commandButton")
        command_button.setDefaultAction(command_action)
        command_button.setText("搜索命令…    Ctrl+Shift+P")
        command_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.menuBar().setCornerWidget(command_button, Qt.Corner.TopRightCorner)
        for dock in (self.toolbox_dock, self.property_dock, self.object_dock, self.output_dock):
            view_menu.addAction(dock.toggleViewAction())
        view_menu.addSeparator()
        for key, title in (("show_grid", "显示网格"), ("snap_to_grid", "吸附网格")):
            action = QAction(title, self)
            action.setIcon(ui_icon("grid" if key == "show_grid" else "snap"))
            action.setIconText("网格" if key == "show_grid" else "吸附")
            action.setToolTip(title)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, member=key: self._guard(lambda: self.set_canvas_setting(member, checked)))
            self.actions[key] = action
            view_menu.addAction(action)
        view_menu.addSeparator()
        original_action = self._action("original_size", "原始大小", self.reset_canvas, "Ctrl+0")
        original_action.setToolTip("恢复 100% 并返回窗口左上方（Ctrl+0）；不修改设计尺寸。")
        view_menu.addAction(original_action)
        fit_action = self._action("fit", "查看全貌", self.fit_canvas, "Ctrl+9")
        fit_action.setIcon(ui_icon("fit"))
        fit_action.setToolTip("临时缩小以查看完整设计（Ctrl+9）；编辑时可恢复原始大小。")
        view_menu.addAction(fit_action)
        view_menu.addAction(self._action("window_properties", "窗口属性", self.select_window))
        view_menu.addSeparator()
        view_menu.addAction(self._action("restore_layout", "恢复默认布局", self.restore_default_layout))
        tools_menu = self.menuBar().addMenu("工具")
        tools_menu.addAction(self._action("menu_editor", "菜单编辑器…", self.edit_menus))
        tools_menu.addAction(self._action("recover", "恢复项目", self.show_recovery))
        settings_menu = self.menuBar().addMenu("设置")
        settings_menu.addAction(self._action("settings", "工作台设置…", self.show_settings, "Ctrl+,"))
        presets_menu = settings_menu.addMenu("布局预设")
        for preset, label in LAYOUTS:
            presets_menu.addAction(self._action("layout_" + preset, label, lambda value=preset: self.set_workbench_layout(value)))
        help_menu = self.menuBar().addMenu("帮助")
        help_menu.addAction(self._action("component_support", "组件支持清单…", self.show_component_support))
        help_menu.addAction(self._action("diagnostics", "导出诊断包…", self.export_diagnostics_dialog))
        help_menu.addAction(self._action("about", "关于", self.show_about))
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addAction(self.actions["show_grid"])
        toolbar.addAction(self.actions["snap_to_grid"])
        toolbar.addSeparator()
        toolbar.addAction(original_action)
        toolbar.addAction(fit_action)
        from panels.value_editors import ChoiceEditor

        self.zoom_combo = ChoiceEditor()
        self.zoom_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        for percent in (25, 50, 75, 100, 125, 150, 200, 300):
            self.zoom_combo.addItem("100% 原大" if percent == 100 else f"{percent}%", percent)
        self.zoom_combo.setCurrentIndex(self.zoom_combo.findData(100))
        self.zoom_combo.setMinimumWidth(100)
        self.zoom_combo.setToolTip("默认 100% 原始大小。滚轮浏览画布；按住控制键滚动可围绕鼠标位置缩放。")
        self.zoom_combo.activated.connect(self._zoom_selected)
        toolbar.addWidget(self.zoom_combo)

    def _build_activity_bar(self) -> None:
        self.activity_bar = QToolBar("面板入口", self)
        self.activity_bar.setObjectName("activityBar")
        self.activity_bar.setMovable(False)
        self.activity_bar.setFloatable(False)
        self.activity_bar.setFixedWidth(48)
        self.activity_bar.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea)
        self.activity_bar.setIconSize(QSize(22, 22))
        self.activity_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.activity_bar)
        for dock, icon in ((self.toolbox_dock, "components"), (self.object_dock, "tree_widget"),
                           (self.property_dock, "settings"), (self.output_dock, "output")):
            action = dock.toggleViewAction()
            action.setIcon(ui_icon(icon))
            action.setToolTip(f"显示 / 隐藏{dock.windowTitle()}")
            self.activity_bar.addAction(action)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.activity_bar.addWidget(spacer)
        self.activity_bar.addAction(self.actions["commands"])

    def show_commands(self) -> None:
        dialog = CommandPalette(self.menuBar(), self)
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                dialog.trigger_selected()
        finally:
            dialog.deleteLater()

    @property
    def page(self) -> CanvasPage | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, CanvasPage) else None

    @property
    def document(self) -> DocumentSession | None:
        return self.page.document if self.page else None

    def _add_document(self, document: DocumentSession) -> CanvasPage:
        page = CanvasPage(document)
        page.canvas.before_interaction = self.properties.commit_pending
        page.window_properties_requested.connect(self.select_window)
        page.canvas.notice.connect(self.statusBar().showMessage)
        page.canvas.error.connect(self.report_error)
        page.canvas.zoom_changed.connect(lambda percent: self._refresh_actions())
        page.canvas.menu_edit_requested.connect(self.edit_menus)
        self.edit_actions.bind_canvas(page.canvas)
        document.status_changed.connect(self._refresh_actions)
        document.status_changed.connect(self.properties.queue_refresh)
        self.tabs.addTab(page, document.model.name)
        self.tabs.setTabIcon(self.tabs.indexOf(page), ui_icon("window"))
        self.tabs.setCurrentWidget(page)
        if self.recovery:
            self.recovery.watch(document)
        self._tab_changed(self.tabs.currentIndex())
        if page.canvas.renderer.plan and page.canvas.renderer.plan.diagnostics:
            self.output.write_message("；".join(page.canvas.renderer.plan.diagnostics))
        return page

    def new_document(self) -> DocumentSession:
        self._new_number += 1
        document = DocumentSession(new_project(f"未命名窗口{self._new_number}"), self.registry, parent=self)
        self._add_document(document)
        return document

    def open_dialog(self) -> None:
        directory = settings_directory(self.settings, "files/default_directory")
        path = choose_project_file(self, directory)
        if path:
            self.open_path(Path(path))

    def open_path(self, path: Path) -> DocumentSession:
        path = path.expanduser().resolve()
        for index in range(self.tabs.count()):
            document = self.tabs.widget(index).document
            if document.path and path_key(document.path) == path_key(path):
                self.tabs.setCurrentIndex(index)
                self._remember_project(path)
                return document
        lease = FileLease(path)
        try:
            loaded = load_project(path)
            compile_plan(loaded.model, self.registry, "加载检查", allow_unknown=True)
            document = DocumentSession(loaded.model, self.registry, saved=not loaded.migrated, parent=self)
            document.path, document.disk_token = path, loaded.token
            document.resource_base = path.parent
            document.read_only = not lease.acquired
            self._add_document(document)
            self.save_service.attach(document, lease)
        except Exception:
            lease.release()
            raise
        if self.persist_settings:
            self.settings.setValue("files/default_directory", str(path.parent))
        message = f"已打开项目：{path.name}"
        if document.read_only:
            message += "；文件正在被使用，当前以只读方式打开，可另存为。"
        self.output.write_message(message)
        self.statusBar().showMessage(message)
        self._remember_project(path)
        self._refresh_actions()
        return document

    def _remember_project(self, path: Path) -> None:
        self._recent_paths = [str(path.resolve())] + [value for value in self._recent_paths if path_key(Path(value)) != path_key(path)]
        self._recent_paths = self._recent_paths[:10]
        if self.persist_settings:
            self.settings.setValue("files/recent", self._recent_paths)
        self._refresh_recent_menu()

    def _refresh_recent_menu(self) -> None:
        self.recent_menu.clear()
        for value in self._recent_paths:
            action = self.recent_menu.addAction(value.replace("&", "&&"))
            action.triggered.connect(lambda checked=False, path=value: self._guard(lambda: self.open_path(Path(path))))
        if self._recent_paths:
            self.recent_menu.addSeparator()
            self.recent_menu.addAction("清空记录", self.clear_recent_projects)
        else:
            self.recent_menu.addAction("暂无最近项目").setEnabled(False)

    def clear_recent_projects(self) -> None:
        self._recent_paths.clear()
        if self.persist_settings:
            self.settings.setValue("files/recent", [])
        self._refresh_recent_menu()

    def restore_default_layout(self) -> None:
        self.set_workbench_layout("standard")
        self.statusBar().showMessage("已恢复组件箱、对象树、属性和输出的默认布局。")

    def set_workbench_layout(self, preset: str) -> None:
        apply_layout_preset(self, preset)
        require(save_workbench(self), "工作台布局保存失败，请检查系统配置目录的写入权限。")
        self.statusBar().showMessage("已切换工作台布局：" + dict(LAYOUTS)[preset])

    def show_settings(self) -> None:
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def export_python_dialog(self) -> None:
        if self.document is None or not self.properties.commit_pending():
            return
        directory = settings_directory(self.settings, "files/export_directory")
        target = QFileDialog.getExistingDirectory(self, "选择 Python 项目导出目录", str(directory),
                                                  QFileDialog.Option.DontUseNativeDialog)
        if target:
            self.export_python_to(Path(target))

    def export_python_to(self, target: Path) -> Path | None:
        if self.document is None or not self.properties.commit_pending():
            return None
        self.page.canvas.cancel_gesture()
        entry = export_project(self.document.model, self.registry, target)
        if self.persist_settings:
            self.settings.setValue("files/export_directory", str(entry.parent))
        message = f"已导出：{entry}；运行此入口即可启动界面，勾选事件的业务代码写入 event_handlers 中的对应函数，初始化代码可写入 handlers.py；重复导出保留已有业务文件。"
        self.output.write_message(message)
        self.output_dock.show()
        self.statusBar().showMessage("代码导出完成。设计项目仍需单独保存。")
        return entry

    def export_diagnostics_dialog(self) -> None:
        target, _ = QFileDialog.getSaveFileName(self, "导出本地诊断包", str(Path.home() / "设计器诊断.zip"),
                                               "诊断压缩包 (*.zip)", options=QFileDialog.Option.DontUseNativeDialog)
        if target:
            path = Path(target)
            if path.suffix.lower() != ".zip":
                path = path.with_name(path.name + ".zip")
            export_diagnostics(path, {"打开项目数": self.tabs.count(), "预览状态": self.preview_service.state,
                                     "未保存项目数": sum(self.tabs.widget(i).document.dirty for i in range(self.tabs.count()))})
            self.output.write_message(f"诊断包已保存：{path}。仅包含环境和异常位置摘要，不包含项目内容，不会自动上传。")
            self.output_dock.show()

    def save_current(self, *, force_as: bool = False) -> bool:
        document = self.document
        if document is None:
            return False
        self.page.canvas.cancel_gesture()
        if not self.properties.commit_pending():
            return False
        return self._save_document(document, force_as=force_as)

    def _save_document(self, document: DocumentSession, *, force_as: bool = False) -> bool:
        if document.saving:
            self.statusBar().showMessage("项目正在保存，请稍候。")
            return False
        target = document.path
        if target is None or force_as or document.read_only:
            directory = settings_directory(self.settings, "files/default_directory")
            initial = target or directory / f"{document.model.name}.uipro"
            value = choose_project_file(self, initial, save=True)
            if not value:
                return False
            target = Path(value)
            if target.suffix.lower() != ".uipro":
                target = target.with_name(target.name + ".uipro")
        self.save_service.save(document, target)
        self.statusBar().showMessage("正在保存项目，可以继续编辑。")
        return True

    def _saved(self, document: DocumentSession, success: bool, message: str) -> None:
        self.output.write_message(message)
        self.statusBar().showMessage(message)
        if success and document.path and self.persist_settings:
            self.settings.setValue("files/default_directory", str(document.path.parent))
        if success and document.path:
            self._remember_project(document.path)
        if success and self.recovery:
            self.recovery.mark_saved(document)
            source = self._recovery_sources.get(document.session_id)
            if source and not document.dirty:
                self.recovery.archive(source)
                self._recovery_sources.pop(document.session_id, None)
            self.refresh_recovery_notice()
        pending = document.session_id in self._pending_close
        self._pending_close.discard(document.session_id)
        if not success:
            self._exit_requested = False
            return
        if pending and not document.dirty:
            self._close_document(document)
        elif pending:
            self.statusBar().showMessage("保存期间产生了新修改，项目继续保持打开。")
            self._exit_requested = False
        if self._exit_requested:
            defer(self, self.close)

    def _tab_changed(self, index: int) -> None:
        if self._switching:
            return
        previous = self.properties.document
        if previous is not None and not previous.closed and previous is not self.document:
            if not self.properties.commit_pending():
                old_page = next((self.tabs.widget(position) for position in range(self.tabs.count())
                                 if self.tabs.widget(position).document is previous), None)
                if old_page:
                    self._switching = True
                    try:
                        self.tabs.setCurrentWidget(old_page)
                    finally:
                        self._switching = False
                return
        for position in range(self.tabs.count()):
            self.tabs.widget(position).canvas.cancel_gesture()
        if self.properties.document is not self.document:
            self.properties.bind(self.document)
            self.object_tree.bind(self.document)
        self._refresh_actions()

    def _refresh_actions(self) -> None:
        document = self.document
        if not self.actions:
            return
        editable = bool(document and not document.read_only and not document.editing_suspended)
        for key in ("save", "save_as", "close", "show_grid", "snap_to_grid", "export_python"):
            self.actions[key].setEnabled(document is not None)
        for key in ("show_grid", "snap_to_grid"):
            self.actions[key].setEnabled(editable)
        self.edit_actions.refresh()
        self.zoom_combo.setEnabled(document is not None)
        self.actions["fit"].setEnabled(document is not None)
        self.actions["original_size"].setEnabled(document is not None)
        self.actions["window_properties"].setEnabled(document is not None)
        self.actions["menu_editor"].setEnabled(editable)
        self.actions["preview"].setEnabled(bool(document and not document.editing_suspended))
        self.actions["export_python"].setEnabled(bool(document and not document.editing_suspended))
        self.actions["stop_preview"].setEnabled(self.preview_service.active)
        self.actions["stop_preview"].setVisible(self.preview_service.active)
        self.actions["preview"].setText("重新预览" if self.preview_service.active else "预览")
        self.welcome.setVisible(document is None)
        self.tabs.setVisible(document is not None)
        self.preview_status.setText("预览运行中" if self.preview_service.active else "设计模式")
        state = ("保存中" if document.saving else "只读" if document.read_only else
                 "未保存" if document.dirty else "已保存") if document else "未打开项目"
        self.document_status.setText(state)
        self.document_status.setToolTip(str(document.path) if document and document.path else "尚未保存到文件")
        if document:
            for key in ("show_grid", "snap_to_grid"):
                self.actions[key].setChecked(document.model.data["canvas"][key])
            percent = self.page.canvas.zoom
            if self.zoom_combo.findData(percent) < 0:
                self.zoom_combo.addItem(f"{percent}%", percent)
            self.zoom_combo.setCurrentIndex(self.zoom_combo.findData(percent))
        for index in range(self.tabs.count()):
            current = self.tabs.widget(index).document
            name = current.path.stem if current.path else current.model.name
            suffix = "（保存中）" if current.saving else "（只读）" if current.read_only else ""
            self.tabs.setTabText(index, name + (" *" if current.dirty else "") + suffix)
            self.tabs.setTabToolTip(index, str(current.path) if current.path else "尚未保存到文件")
        self.setWindowTitle(f"{document.model.name} · 中文界面设计器" if document else "中文界面设计器")

    def undo(self) -> None:
        self.edit_actions.undo()

    def redo(self) -> None:
        self.edit_actions.redo()

    def delete_selected(self) -> None:
        self.edit_actions.delete()

    def _create_component(self, type_id: str) -> None:
        if self.page:
            self.page.canvas.create_component(type_id)

    def _zoom_selected(self, index: int) -> None:
        if self.page:
            self._guard(lambda: self.page.canvas.set_zoom(self.zoom_combo.itemData(index)))

    def fit_canvas(self) -> None:
        if self.page:
            self.page.canvas.fit_to_window()

    def reset_canvas(self) -> None:
        if self.page:
            self.page.canvas.reset_view()

    def preview_current(self) -> None:
        document = self.document
        if document is None:
            return
        self.page.canvas.cancel_gesture()
        if not self.properties.commit_pending():
            return
        self.preview_service.start(document.model, document.state_id, document.session_id)

    def _preview_notice(self, message: str) -> None:
        self.output.write_message(message)
        self.statusBar().showMessage(message)

    def select_window(self) -> None:
        if self.document and self.properties.commit_pending():
            self.document.select(self.document.model.root_id)
            self.property_dock.show()
            self.property_dock.raise_()

    def edit_menus(self) -> None:
        document = self.document
        if document is None or document.read_only or document.editing_suspended:
            return
        self.page.canvas.cancel_gesture()
        if not self.properties.commit_pending():
            return
        baseline = document.model
        dialog = None
        try:
            dialog = MenuEditor(baseline, self.registry, self, selected_id=document.selected_id)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                require(not document.closed and document.model == baseline, "项目已变化，请重新打开菜单编辑器。")
                document.execute("编辑菜单", lambda model: dialog.model)
                if dialog.selected_id in document.model.nodes:
                    document.select(dialog.selected_id)
        except DesignerError as exc:
            self.report_error(str(exc))
        finally:
            if dialog is not None:
                dialog.deleteLater()

    def _object_double_clicked(self, item, column) -> None:
        if self.document and self.document.model.nodes[self.document.selected_id].slot in {"menu_bar", "menu"}:
            self.edit_menus()

    def set_canvas_setting(self, key: str, value: bool) -> None:
        from dataclasses import replace

        if self.document:
            if not self.properties.commit_pending():
                return
            self.page.canvas.cancel_gesture()
            self.document.execute("修改画布设置", lambda model: replace(model, data=model.data.changed(
                canvas=model.data["canvas"].changed(**{key: value}))))

    def report_error(self, message: str) -> None:
        self.output.write_message("错误：" + message)
        self.statusBar().showMessage(message)
        self.output_dock.show()

    def _guard(self, operation: Callable[[], object]) -> None:
        try:
            operation()
        except DesignerError as exc:
            self.report_error(str(exc))
        except Exception:
            logger.exception("界面操作失败。")
            self.report_error("操作未完成，详细原因已记录到诊断日志。")

    def request_close(self, index: int) -> bool:
        if index < 0 or index >= self.tabs.count():
            return True
        page = self.tabs.widget(index)
        document = page.document
        page.canvas.cancel_gesture()
        if document is self.document and not self.properties.commit_pending():
            self._exit_requested = False
            return False
        if document.saving:
            self._pending_close.add(document.session_id)
            self.statusBar().showMessage("保存完成后关闭项目。")
            return False
        if document.dirty:
            choice = ask_save(self, document.model.name)
            if choice == "cancel":
                self._exit_requested = False
                return False
            if choice == "save":
                try:
                    if self._save_document(document):
                        self._pending_close.add(document.session_id)
                    else:
                        self._exit_requested = False
                except DesignerError as exc:
                    self.report_error(str(exc))
                    self._exit_requested = False
                return False
        self._close_document(document)
        return True

    def _close_document(self, document: DocumentSession) -> None:
        page = next((self.tabs.widget(index) for index in range(self.tabs.count())
                     if self.tabs.widget(index).document is document), None)
        if page is None:
            return
        self.preview_service.stop_session(document.session_id)
        self.save_service.release(document)
        if self.recovery:
            self.recovery.dismiss(document)
            source = self._recovery_sources.pop(document.session_id, None)
            if source:
                self.recovery.archive(source)
        if document is self.document:
            self.properties.bind(None)
            self.object_tree.bind(None)
        page.dispose()
        document.close()
        document.status_changed.disconnect(self._refresh_actions)
        document.status_changed.disconnect(self.properties.queue_refresh)
        self.tabs.removeTab(self.tabs.indexOf(page))
        page.deleteLater()
        document.deleteLater()
        self._refresh_actions()

    def refresh_recovery_notice(self) -> None:
        paths = self.recovery.discover() if self.recovery else []
        self.recovery_button.setVisible(bool(paths))
        self.recovery_button.setText(f"发现 {len(paths)} 份恢复记录，单击查看")

    def show_recovery(self) -> None:
        paths = self.recovery.discover() if self.recovery else []
        if not paths:
            self.statusBar().showMessage("目前没有可恢复的项目。")
            return
        path = choose_recovery(self, paths)
        if path:
            self._guard(lambda: self.restore_project(path))

    def restore_project(self, path: Path) -> DocumentSession:
        loaded = load_project(path)
        compile_plan(loaded.model, self.registry, "恢复检查", allow_unknown=True)
        document = DocumentSession(loaded.model, self.registry, parent=self)
        document.resource_base = path.parent
        self._add_document(document)
        self._recovery_sources[document.session_id] = path
        self.output.write_message("恢复内容已作为未保存副本打开，请选择保存位置。")
        return document

    def show_component_support(self) -> None:
        dialog = SupportDialog(self.registry, self)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def show_about(self) -> None:
        box = QMessageBox(self)
        try:
            box.setWindowTitle("关于中文界面设计器")
            box.setText(f"中文界面设计器 {VERSION} · {CHANNEL}")
            count = sum(spec.toolbox for spec in self.registry.specs.values())
            box.setInformativeText(f"支持 {count} 类可拖放组件、容器嵌套、中文属性、框选多选、批量排版、整树复制删除、保存加载、撤销重做、独立预览和 Python 项目导出。\n"
                                   "详细范围见“帮助 → 组件支持清单”。属性中的事件可勾选连接，取消勾选即断开；业务逻辑写入导出目录 event_handlers 中的对应函数，重复导出保留已有代码。")
            box.addButton("关闭", QMessageBox.ButtonRole.AcceptRole)
            box.exec()
        finally:
            box.deleteLater()

    def discard_all_for_test(self) -> None:
        """自动化测试只关闭自己建立的测试会话，不写入项目。"""
        while self.tabs.count():
            self._close_document(self.tabs.widget(0).document)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._closed:
            event.accept()
            return
        self._exit_requested = True
        while self.tabs.count():
            if not self.request_close(self.tabs.count() - 1):
                event.ignore()
                return
        if self.persist_settings:
            self.settings.setValue("window/geometry", self.saveGeometry())
            if not save_workbench(self):
                logger.warning("工作台设置未能保存。")
        self.save_service.shutdown()
        self.preview_service.shutdown()
        if self.recovery:
            self.recovery.shutdown()
        self.edit_actions.dispose()
        self.output.dispose()
        self._closed = True
        event.accept()
