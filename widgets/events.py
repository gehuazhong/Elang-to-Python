"""内置组件的中文信号与通用交互事件；声明可由真实元对象逐项核对。"""

from __future__ import annotations

from core.metadata import EventSpec


OBJECT_SIGNALS = (("destroyed", "即将销毁"), ("objectNameChanged", "名称改变"))
WIDGET_SIGNALS = (("windowTitleChanged", "窗口标题改变"), ("windowIconChanged", "窗口图标改变"),
                  ("windowIconTextChanged", "窗口图标文字改变"), ("customContextMenuRequested", "请求快捷菜单"))
BUTTON_SIGNALS = (("pressed", "被按下"), ("released", "被放开"), ("clicked", "被单击"), ("toggled", "选中状态改变"))
SLIDER_SIGNALS = (("valueChanged", "值改变"), ("sliderPressed", "滑块按下"), ("sliderMoved", "滑块移动"),
                  ("sliderReleased", "滑块放开"), ("rangeChanged", "范围改变"), ("actionTriggered", "步进操作"))
SPIN_SIGNALS = (("editingFinished", "编辑完成"), ("returnPressed", "按下回车"))
VIEW_SIGNALS = (("pressed", "索引被按下"), ("clicked", "索引被单击"), ("doubleClicked", "索引被双击"),
                ("activated", "索引被激活"), ("entered", "鼠标进入索引"), ("viewportEntered", "鼠标进入空白区"),
                ("iconSizeChanged", "图标尺寸改变"))
ITEM_SIGNALS = (("itemPressed", "表项被按下"), ("itemClicked", "表项被单击"), ("itemDoubleClicked", "被双击"),
                ("itemActivated", "表项被激活"), ("itemEntered", "鼠标进入表项"), ("itemChanged", "内容改变"),
                ("currentItemChanged", "当前表项改变"), ("itemSelectionChanged", "选择改变"))
TREE_SIGNALS = (("expanded", "索引展开"), ("collapsed", "索引折叠"),
                ("itemExpanded", "表项展开"), ("itemCollapsed", "表项折叠"))
DATE_SIGNALS = (("dateTimeChanged", "日期时间改变"), ("dateChanged", "日期改变"), ("timeChanged", "时间改变"))
RICH_TEXT_SIGNALS = (("textChanged", "文本改变"), ("undoAvailable", "可撤销状态改变"),
                     ("redoAvailable", "可重做状态改变"), ("currentCharFormatChanged", "文字格式改变"),
                     ("copyAvailable", "可复制状态改变"), ("selectionChanged", "选择改变"),
                     ("cursorPositionChanged", "光标位置改变"))

COMMON_EVENTS = (
    ("mouse_press", "鼠标按下", "MouseButtonPress"), ("mouse_release", "鼠标放开", "MouseButtonRelease"),
    ("mouse_double_click", "鼠标双击", "MouseButtonDblClick"), ("mouse_move", "鼠标移动", "MouseMove"),
    ("mouse_enter", "鼠标进入", "Enter"), ("mouse_leave", "鼠标离开", "Leave"),
    ("mouse_wheel", "鼠标滚轮", "Wheel"), ("key_press", "按键按下", "KeyPress"),
    ("key_release", "按键放开", "KeyRelease"), ("focus_in", "获得焦点", "FocusIn"),
    ("focus_out", "失去焦点", "FocusOut"), ("show", "被显示", "Show"), ("hide", "被隐藏", "Hide"),
    ("resize", "尺寸改变", "Resize"), ("move", "位置改变", "Move"), ("close", "窗口关闭", "Close"),
    ("window_activate", "窗口激活", "WindowActivate"), ("window_deactivate", "窗口失活", "WindowDeactivate"),
    ("context_menu", "快捷菜单事件", "ContextMenu"), ("paint", "重绘", "Paint"),
    ("input_method", "输入法输入", "InputMethod"), ("drag_enter", "拖动进入", "DragEnter"),
    ("drag_move", "拖动移动", "DragMove"), ("drag_leave", "拖动离开", "DragLeave"), ("drop", "拖放落下", "Drop"),
)

# 半选状态采用新版枚举信号；旧整数信号仅为兼容保留，不重复暴露。
EXCLUDED_SIGNALS = {"QCheckBox": {"stateChanged"}}


def events_for(qt_class: str, declared: tuple[EventSpec, ...] = ()) -> tuple[EventSpec, ...]:
    signals = []
    from .advanced import NONVISUAL_CLASSES
    visual = qt_class not in {"QTimer", "CommonDialog", "QAction"} | NONVISUAL_CLASSES
    if qt_class in {"QPushButton", "QToolButton", "QCommandLinkButton", "QCheckBox", "QRadioButton"}:
        signals.extend(BUTTON_SIGNALS)
    additions = {
        "QAction": (("triggered", "被单击"), ("toggled", "选中状态改变"), ("hovered", "鼠标移入"),
                    ("changed", "属性改变"), ("enabledChanged", "启用状态改变"), ("visibleChanged", "可视状态改变"),
                    ("checkableChanged", "可选中状态改变")),
        "QMenuBar": (("triggered", "菜单被单击"), ("hovered", "菜单被悬停")),
        "QMainWindow": (("iconSizeChanged", "图标尺寸改变"), ("toolButtonStyleChanged", "工具按钮样式改变"),
                        ("tabifiedDockWidgetActivated", "停靠面板激活")),
        "QLabel": (("linkActivated", "链接被单击"), ("linkHovered", "鼠标悬停链接")),
        "QLineEdit": (("textChanged", "文本改变"), ("textEdited", "用户编辑文本"), ("cursorPositionChanged", "光标位置改变"),
                      ("returnPressed", "按下回车"), ("editingFinished", "编辑完成"),
                      ("selectionChanged", "选择改变"), ("inputRejected", "输入被拒绝")),
        "QPlainTextEdit": (("textChanged", "文本改变"), ("undoAvailable", "可撤销状态改变"), ("redoAvailable", "可重做状态改变"),
                          ("copyAvailable", "可复制状态改变"), ("selectionChanged", "选择改变"),
                          ("cursorPositionChanged", "光标位置改变"), ("updateRequest", "请求更新区域"),
                          ("blockCountChanged", "文本段数改变"), ("modificationChanged", "修改状态改变")),
        "QComboBox": (("currentIndexChanged", "选择改变"), ("currentTextChanged", "当前文本改变"),
                      ("editTextChanged", "文本改变"), ("activated", "选项确认"), ("textActivated", "选项文字确认"),
                      ("highlighted", "选项高亮"), ("textHighlighted", "选项文字高亮")),
        "QCheckBox": (("checkStateChanged", "选择改变"),),
        "QToolButton": (("triggered", "动作被触发"),),
        "QGroupBox": (("clicked", "被单击"), ("toggled", "选中状态改变")),
        "QProgressBar": (("valueChanged", "值改变"),),
        "QCalendarWidget": (("selectionChanged", "选择改变"), ("clicked", "被单击"),
                            ("activated", "日期确认"), ("currentPageChanged", "显示月份改变")),
        "QLCDNumber": (("overflow", "显示溢出"),),
        "QToolBar": (("actionTriggered", "按钮被单击"), ("movableChanged", "允许移动改变"),
                     ("allowedAreasChanged", "允许停靠区域改变"), ("orientationChanged", "方向改变"),
                     ("iconSizeChanged", "图标尺寸改变"), ("toolButtonStyleChanged", "工具按钮样式改变"),
                     ("topLevelChanged", "浮动状态改变"), ("visibilityChanged", "可见状态改变")),
        "QStatusBar": (("messageChanged", "文本改变"),),
        "SelectionTabs": (("tabBarClicked", "页签被单击"), ("tabBarDoubleClicked", "页签被双击"),
                          ("tabCloseRequested", "页签关闭请求"), ("tabMoved", "页签顺序改变")),
        "QStackedWidget": (("widgetAdded", "页面加入"), ("widgetRemoved", "页面移除")),
        "QDockWidget": (("allowedAreasChanged", "允许停靠区域改变"), ("dockLocationChanged", "停靠位置改变"),
                        ("featuresChanged", "窗口能力改变")),
        "QMdiSubWindow": (("aboutToActivate", "即将激活"),),
        "QWizard": (("customButtonClicked", "自定义按钮被单击"), ("finished", "向导关闭"),
                    ("helpRequested", "请求帮助"), ("pageAdded", "页面加入"), ("pageRemoved", "页面移除")),
        "QTabBar": (("tabBarClicked", "页签被单击"), ("tabBarDoubleClicked", "页签被双击")),
        "QButtonGroup": (("buttonClicked", "按钮被单击"), ("buttonPressed", "按钮被按下"),
                         ("buttonReleased", "按钮被放开"), ("buttonToggled", "按钮选中改变"),
                         ("idPressed", "成员被按下"), ("idReleased", "成员被放开")),
        "QGraphicsView": (("rubberBandChanged", "框选区域改变"),),
    }
    signals.extend(additions.get(qt_class, ()))
    if qt_class in {"QListView", "QTableView", "QTreeView", "QColumnView", "QUndoView"}:
        signals.extend(VIEW_SIGNALS)
        if qt_class in {"QListView", "QUndoView"}:
            signals.append(("indexesMoved", "项目位置改变"))
        if qt_class == "QTreeView":
            signals.extend((("expanded", "索引展开"), ("collapsed", "索引折叠")))
        if qt_class == "QColumnView":
            signals.append(("updatePreviewWidget", "预览项目改变"))
    if qt_class in {"QTextEdit", "QTextBrowser"}:
        signals.extend(RICH_TEXT_SIGNALS)
        if qt_class == "QTextBrowser":
            signals.extend((("anchorClicked", "链接被单击"), ("highlighted", "鼠标悬停链接"),
                            ("sourceChanged", "页面来源改变"), ("backwardAvailable", "可后退状态改变"),
                            ("forwardAvailable", "可前进状态改变"), ("historyChanged", "浏览历史改变")))
    if qt_class == "QFontComboBox":
        signals.extend(additions["QComboBox"] + (("currentFontChanged", "字体改变"),))
    if qt_class == "QKeySequenceEdit":
        signals.extend((("keySequenceChanged", "快捷键改变"), ("editingFinished", "编辑完成")))
    if qt_class in {"QSlider", "QDial", "QScrollBar"}:
        signals.extend(SLIDER_SIGNALS)
    if qt_class in {"QSpinBox", "QDoubleSpinBox"}:
        signals.extend(SPIN_SIGNALS + (("valueChanged", "值改变"), ("textChanged", "文本改变")))
    if qt_class in {"QDateEdit", "QTimeEdit", "QDateTimeEdit"}:
        signals.extend(SPIN_SIGNALS + DATE_SIGNALS)
        if qt_class != "QDateTimeEdit":
            signals.append(("userDateChanged" if qt_class == "QDateEdit" else "userTimeChanged", "用户值改变"))
    if qt_class in {"QListWidget", "QTableWidget", "QTreeWidget", "SuperList"}:
        signals.extend(VIEW_SIGNALS + ITEM_SIGNALS)
        if qt_class in {"QTreeWidget", "SuperList"}:
            signals.extend(TREE_SIGNALS)
        elif qt_class == "QListWidget":
            signals.extend((("indexesMoved", "项目位置改变"), ("currentTextChanged", "当前文本改变"), ("currentRowChanged", "当前行改变")))
        else:
            signals.extend((("cellPressed", "单元格被按下"), ("cellClicked", "单元格被单击"),
                            ("cellDoubleClicked", "单元格被双击"), ("cellActivated", "单元格被激活"),
                            ("cellEntered", "鼠标进入单元格"), ("cellChanged", "单元格内容改变"),
                            ("currentCellChanged", "当前单元格改变")))
    preserved = {event.qt_signal: event for event in declared}
    reserved = {event.key for event in declared}
    events = [preserved.get(signal, EventSpec("signal_" + signal if signal in reserved else signal, label, signal))
              for signal, label in signals]
    existing = {event.qt_signal for event in events}
    events.extend(event for event in declared if event.qt_signal not in existing)
    if qt_class == "QRadioButton":
        events = [EventSpec(event.key, "选择改变", event.qt_signal) if event.key == "toggled" else event for event in events]
    if qt_class in {"QDateEdit", "QTimeEdit", "QDateTimeEdit"}:
        primary = {"QDateEdit": "dateChanged", "QTimeEdit": "timeChanged", "QDateTimeEdit": "dateTimeChanged"}[qt_class]
        events = [EventSpec(event.key, "值改变", event.qt_signal) if event.key == primary else event for event in events]
    if visual:
        events.extend(EventSpec(key, label, qt_event=kind) for key, label, kind in COMMON_EVENTS)
        events.extend(EventSpec(signal, label, signal) for signal, label in WIDGET_SIGNALS)
    events.extend(EventSpec(signal, label, signal) for signal, label in OBJECT_SIGNALS)
    return tuple(events)
