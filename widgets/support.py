"""Qt 控件清单与设计器支持矩阵；已接入能力由注册表计算。"""

from __future__ import annotations

from dataclasses import dataclass

from core.registry import WidgetRegistry


# 以已安装的 Qt 六点十一版本为核对基线，基类和内部辅助类单独标记。
WIDGET_INVENTORY: tuple[tuple[str, str, str], ...] = (
    ("QAbstractButton", "抽象按钮", "基类"), ("QAbstractItemView", "抽象项目视图", "基类"),
    ("QAbstractScrollArea", "抽象滚动区域", "基类"), ("QAbstractSlider", "抽象滑动控件", "基类"),
    ("QAbstractSpinBox", "抽象数值输入", "基类"), ("QCalendarWidget", "日历", "日期时间"),
    ("QCheckBox", "选择框", "选择"), ("QColorDialog", "颜色对话框", "对话框"),
    ("QColumnView", "分栏视图", "数据视图"), ("QComboBox", "组合框", "选择"),
    ("QCommandLinkButton", "命令链接按钮", "按钮"), ("QDateEdit", "日期编辑框", "日期时间"),
    ("QDateTimeEdit", "日期时间编辑框", "日期时间"), ("QDial", "旋钮", "输入"),
    ("QDialog", "对话框窗口", "窗口"), ("QDialogButtonBox", "对话框按钮组", "按钮"),
    ("QDockWidget", "停靠窗口", "窗口结构"), ("QDoubleSpinBox", "小数输入框", "输入"),
    ("QErrorMessage", "错误消息框", "对话框"), ("QFileDialog", "文件对话框", "对话框"),
    ("QFocusFrame", "焦点边框", "内部辅助"), ("QFontComboBox", "字体组合框", "选择"),
    ("QFontDialog", "字体对话框", "对话框"), ("QFrame", "边框容器", "容器"),
    ("QGraphicsView", "图形视图", "图形"), ("QGroupBox", "分组框", "容器"),
    ("QHeaderView", "表头视图", "内部辅助"), ("QInputDialog", "输入对话框", "对话框"),
    ("QKeySequenceEdit", "快捷键编辑框", "输入"), ("QLCDNumber", "液晶数字", "显示"),
    ("QLabel", "标签", "显示"), ("QLineEdit", "单行编辑框", "输入"),
    ("QListView", "列表模型视图", "数据视图"), ("QListWidget", "列表框", "数据视图"),
    ("QMainWindow", "主窗口", "窗口结构"), ("QMdiArea", "多文档区域", "容器"),
    ("QMdiSubWindow", "多文档子窗口", "窗口结构"), ("QMenu", "菜单", "窗口结构"),
    ("QMenuBar", "菜单栏", "窗口结构"), ("QMessageBox", "消息框", "对话框"),
    ("QPlainTextEdit", "多行编辑框", "输入"), ("QProgressBar", "进度条", "显示"),
    ("QProgressDialog", "进度对话框", "对话框"), ("QPushButton", "按钮", "按钮"),
    ("QRadioButton", "单选框", "选择"), ("QRhiWidget", "硬件渲染控件", "图形"),
    ("QRubberBand", "橡皮筋选框", "内部辅助"), ("QScrollArea", "滚动区域", "容器"),
    ("QScrollBar", "滚动条", "输入"), ("QSizeGrip", "尺寸调整角", "内部辅助"),
    ("QSlider", "滑块", "输入"), ("QSpinBox", "数值输入框", "输入"),
    ("QSplashScreen", "启动画面", "窗口"), ("QSplitter", "分隔容器", "容器"),
    ("QSplitterHandle", "分隔手柄", "内部辅助"), ("QStackedWidget", "堆叠容器", "容器"),
    ("QStatusBar", "状态栏", "窗口结构"), ("QTabBar", "选项卡栏", "窗口结构"),
    ("QTabWidget", "选项卡容器", "容器"), ("QTableView", "表格模型视图", "数据视图"),
    ("QTableWidget", "表格", "数据视图"), ("QTextBrowser", "文本浏览器", "显示"),
    ("QTextEdit", "富文本编辑框", "输入"), ("QTimeEdit", "时间编辑框", "日期时间"),
    ("QToolBar", "工具栏", "窗口结构"), ("QToolBox", "折叠页容器", "容器"),
    ("QToolButton", "工具按钮", "按钮"), ("QTreeView", "树形模型视图", "数据视图"),
    ("QTreeWidget", "树形框", "数据视图"), ("QUndoView", "撤销历史视图", "数据视图"),
    ("QWidget", "基础工作区", "窗口结构"), ("QWizard", "向导窗口", "窗口"),
    ("QWizardPage", "向导页面", "容器"),
)
EXTRA_INVENTORY = (
    ("QTimer", "定时器", "非可视", "需要对象托盘、生命周期及超时绑定。"),
    ("QAction", "动作", "非可视", "需要菜单、工具栏及快捷键的共享动作模型。"),
    ("QButtonGroup", "按钮组", "非可视", "需要显式分组关系；当前单选框按父容器互斥。"),
    ("QHBoxLayout", "水平布局", "自动布局", "需要布局接管几何、间距和子控件排列规则。"),
    ("QVBoxLayout", "垂直布局", "自动布局", "需要布局接管几何、间距和子控件排列规则。"),
    ("QGridLayout", "网格布局", "自动布局", "需要行列、跨行跨列和伸缩规则。"),
    ("QFormLayout", "表单布局", "自动布局", "需要标签与字段配对的布局模型。"),
    ("QSpacerItem", "弹性空白", "自动布局", "需要自动布局管理空白尺寸和伸缩。"),
    ("QLabel", "图片框", "资源组件", "需要图片导入、相对路径、缺失提示和随代码导出。"),
    ("QOpenGLWidget", "三维绘图控件", "扩展模块", "属于独立模块，需要图形上下文和预览支持。"),
    ("QSvgWidget", "矢量图控件", "扩展模块", "属于独立模块，需要矢量资源支持。"),
    ("QWebEngineView", "网页控件", "扩展模块", "属于独立模块，需要进程、网络和发行依赖支持。"),
)


@dataclass(frozen=True, slots=True)
class SupportRow:
    qt_class: str
    label: str
    category: str
    status: str
    property_count: int
    events: str
    parenting: str
    persistence: str
    preview: str
    export: str
    note: str
    type_id: str = ""


def support_rows(registry: WidgetRegistry) -> tuple[SupportRow, ...]:
    registered = {spec.qt_class: spec for spec in registry.specs.values() if spec.slot != "pages" or spec.toolbox}
    registered["QTabWidget"] = registry.require("builtin.tab_widget")
    registered["QFileDialog"] = registry.require("builtin.common_dialog")
    result = []
    for cls, label, category in WIDGET_INVENTORY:
        spec = registered.get(cls)
        if spec:
            result.append(SupportRow(cls, spec.label, category, "已接入" if spec.toolbox else "窗口结构", len(spec.properties),
                "、".join(event.label for event in spec.events) or "无事件提示",
                "分页面嵌套" if spec.type_id == "builtin.tab_widget" else "支持嵌套" if spec.can_contain else
                "非可视组件" if spec.slot == "non_visual" else "固定挂接窗口" if spec.slot in {"root", "tool_bar", "status_bar", "menu_bar"} else "叶子控件",
                "已接入", "已接入", "已接入", ("使用页签栏与页面组合适配；" if spec.type_id == "builtin.tab_widget" else "") +
                "仅列出的属性已支持；事件可勾选，预览报告触发，导出自动连接处理函数。", spec.type_id))
        elif cls == "QMenu":
            result.append(SupportRow(cls, label, category, "窗口结构", 0, "由菜单项设置", "菜单编辑器管理层级",
                                     "已接入", "已接入", "已接入", "增加子菜单自动创建；通过菜单项统一设置属性和事件。"))
        else:
            status = "非独立组件" if category in {"基类", "内部辅助"} else "待接入"
            note = "供其他组件继承或内部使用，不作为独立拖放目标。" if status == "非独立组件" else {
                "容器": "需要专属页面、滚动或布局管理规则。", "数据视图": "需要数据模型与编辑策略。",
                "对话框": "需要独立窗口、触发入口和结果返回规则。",
                "窗口结构": "需要专属挂接位置，不能作为普通矩形控件处理。",
            }.get(category, "需要完整属性适配、交互与导出验证。")
            result.append(SupportRow(cls, label, category, status, 0, "未接入", "未接入", "未接入", "未接入", "未接入", note))
    for cls, label, category, note in EXTRA_INVENTORY:
        if cls == "QAction":
            spec = registry.require("builtin.menu_item")
            result.append(SupportRow(cls, spec.label, category, "窗口结构", len(spec.properties),
                                     "、".join(e.label for e in spec.events), "菜单编辑器管理层级",
                                     "已接入", "已接入", "已接入", "通过工具菜单或窗口属性打开菜单编辑器。", spec.type_id))
            continue
        spec = registry.get("builtin.picture_box") if label == "图片框" else registered.get(cls)
        if spec:
            result.append(SupportRow(cls, spec.label, category, "已接入", len(spec.properties), "、".join(e.label for e in spec.events),
                         "非可视组件" if spec.slot == "non_visual" else "叶子控件", "已接入", "已接入", "已接入",
                         "图片作为静态快照嵌入项目。" if label == "图片框" else "支持列出的属性、预览和独立导出。", spec.type_id))
        else:
            result.append(SupportRow(cls, label, category, "待接入", 0, "未接入", "未接入", "未接入", "未接入", "未接入", note))
    for key, cls, note in (("drawing_board", "QWidget + QPainter", "运行时绘画；画笔、底图和底色可设计。"),
                           ("super_list", "QTreeWidget", "报表式多列列表，支持勾选、排序和整行选择。")):
        spec = registry.require("builtin." + key)
        result.append(SupportRow(cls, spec.label, "组合适配", "已接入", len(spec.properties), "、".join(e.label for e in spec.events),
                      "叶子控件", "已接入", "已接入", "已接入", note, spec.type_id))
    return tuple(result)


def support_markdown(registry: WidgetRegistry) -> str:
    lines = ["# 组件支持矩阵", "", "本表由注册表和已核对的 Qt 控件目录生成，不把抽象基类当作可拖放组件。", "",
             f"QtWidgets 基线包含 {len(WIDGET_INVENTORY)} 个 QWidget 体系类；当前组件箱接入 {sum(spec.toolbox for spec in registry.specs.values())} 类。",
             "非可视对象、自动布局和扩展模块另列；本表不声称覆盖整个 Qt 的所有模块。", "",
             "已接入表示列明的属性和流程已实现，不表示暴露了该 Qt 类的全部属性。中文事件支持勾选连接、保存、撤销与导出处理函数；预览只报告触发，不执行业务文件。", "",
             "| 中文名称 | Qt 类 | 分类 | 状态 | 属性数 | 可勾选事件 | 容器规则 | 保存加载 | 预览 | 导出 | 说明 |",
             "| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- |"]
    for row in support_rows(registry):
        lines.append(f"| {row.label} | {row.qt_class} | {row.category} | {row.status} | {row.property_count} | {row.events} | {row.parenting} | {row.persistence} | {row.preview} | {row.export} | {row.note} |")
    lines += ["", "## 已接入属性明细", ""]
    for spec in registry.specs.values():
        lines += ["### " + spec.label, "", "| 中文属性 | 稳定字段 | 类型 | Qt 属性或适配 |", "| --- | --- | --- | --- |"]
        types = {"string": "文本", "multiline": "多行文本", "bool": "布尔", "int": "整数", "float": "小数", "enum": "枚举",
                 "color": "颜色", "image": "图片快照", "date": "日期", "time": "时间", "datetime": "日期时间", "string_list": "文本列表", "table": "表格", "tree": "节点树", "shortcut": "快捷键"}
        for prop in spec.properties:
            lines.append(f"| {prop.label} | {prop.key} | {types[prop.value_type]} | {prop.qt_name or '复合适配'} |")
        lines += ["", "| 中文事件 | 稳定字段 | Qt 信号或事件 |", "| --- | --- | --- |"]
        for event in spec.events:
            lines.append(f"| {event.label} | {event.key} | {event.qt_signal or event.qt_event} |")
        lines.append("")
    return "\n".join(lines)
