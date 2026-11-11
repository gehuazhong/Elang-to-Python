"""Remaining public widgets, layout containers, and runtime services."""

from core.metadata import EventSpec as E, PropertySpec as P, WidgetSpec
from core.registry import WidgetRegistry


ADVANCED_TYPES = {
    "horizontal_layout": "QHBoxLayout", "vertical_layout": "QVBoxLayout",
    "grid_layout": "QGridLayout", "form_layout": "QFormLayout", "spacer": "QSpacerItem",
    "scroll_area": "QScrollArea", "splitter": "QSplitter", "stacked_widget": "QStackedWidget",
    "tool_box": "QToolBox", "mdi_area": "QMdiArea", "wizard_page": "QWizardPage",
    "dialog": "QDialog", "dock_widget": "QDockWidget", "mdi_subwindow": "QMdiSubWindow",
    "wizard": "QWizard", "splash_screen": "QSplashScreen", "tab_bar": "QTabBar",
    "message_box": "QMessageBox", "error_message": "QErrorMessage", "input_dialog": "QInputDialog",
    "color_dialog": "QColorDialog", "font_dialog": "QFontDialog", "progress_dialog": "QProgressDialog",
    "list_view": "QListView", "table_view": "QTableView", "tree_view": "QTreeView",
    "column_view": "QColumnView", "undo_view": "QUndoView",
    "dialog_button_box": "QDialogButtonBox", "button_group": "QButtonGroup",
    "graphics_view": "QGraphicsView", "rhi_widget": "QRhiWidget", "opengl_widget": "QOpenGLWidget",
    "svg_widget": "QSvgWidget", "web_view": "QWebEngineView",
}
NONVISUAL_CLASSES = frozenset({"QMessageBox", "QErrorMessage", "QInputDialog", "QColorDialog",
                              "QFontDialog", "QProgressDialog", "QButtonGroup"})
LAYOUT_TYPES = frozenset("builtin." + key for key in
                        ("horizontal_layout", "vertical_layout", "grid_layout", "form_layout"))
PAGE_TYPES = frozenset({"builtin.tab_widget", "builtin.stacked_widget", "builtin.tool_box", "builtin.wizard"})
LAYOUT_ITEM_PROPERTIES = (
    P("layout_stretch", "布局伸缩", "布局项", "int", 0, maximum=1000),
    P("layout_row", "布局行", "布局项", "int", -1, minimum=-1, maximum=999,
      description="从零开始；负一表示按对象顺序自动排列。"),
    P("layout_column", "布局列", "布局项", "int", -1, minimum=-1, maximum=999),
    P("layout_row_span", "跨行数", "布局项", "int", 1, minimum=1, maximum=100),
    P("layout_column_span", "跨列数", "布局项", "int", 1, minimum=1, maximum=100),
)


def register_advanced_widgets(registry: WidgetRegistry, common: tuple[P, ...]) -> None:
    def add(key, label, group, size, props=(), *, container=False, slot="children", events=()):
        registry.register(WidgetSpec("builtin." + key, label, group, ADVANCED_TYPES[key], 1,
                                     slot, size, key, tuple(props) + (common if slot != "non_visual" else ()),
                                     can_contain=container,
                                     events=tuple(E(signal, text, signal) for signal, text in events)))

    def enum(key, label, default, options, group="行为"):
        return P(key, label, group, "enum", default, options=options)

    orientation = enum("orientation", "方向", "horizontal", (("horizontal", "水平"), ("vertical", "垂直")))
    trigger = P("trigger_control", "触发按钮", "行为", "string", "",
                description="预览和导出时连接所选按钮；不绑定时由业务代码调用 open_dialog()。")
    title = P("title", "标题", "基本", "string", "窗口")
    margins = tuple(P("content_" + side, label, "容器", "int", 8, maximum=1000)
                    for side, label in (("left", "左内边距"), ("top", "上内边距"),
                                        ("right", "右内边距"), ("bottom", "下内边距")))
    spacing = P("spacing", "控件间距", "布局", "int", 8, maximum=1000)
    for key, label in (("horizontal_layout", "水平布局"), ("vertical_layout", "垂直布局"),
                       ("grid_layout", "网格布局"), ("form_layout", "表单布局")):
        props = margins + (spacing,)
        if key == "grid_layout":
            props += (P("columns", "自动排列列数", "布局", "int", 2, minimum=1, maximum=100),)
        add(key, label, "自动布局", (360, 240), props, container=True)
    add("spacer", "弹性空白", "自动布局", (40, 40), (
        orientation, P("minimum_extent", "最小长度", "布局", "int", 0, maximum=16384),
        P("expanding", "允许伸展", "布局", "bool", True)))
    add("scroll_area", "滚动区域", "容器组件", (360, 260), (
        P("content_width", "内容宽度", "容器", "int", 640, minimum=1, maximum=16384),
        P("content_height", "内容高度", "容器", "int", 480, minimum=1, maximum=16384),
        P("widget_resizable", "内容随区域伸缩", "容器", "bool", False),
        P("scroll_x", "初始水平滚动", "容器", "int", 0, maximum=16384),
        P("scroll_y", "初始垂直滚动", "容器", "int", 0, maximum=16384),
        enum("horizontal_policy", "水平滚动条", "as_needed", (("as_needed", "需要时显示"), ("always", "始终显示"), ("never", "隐藏"))),
        enum("vertical_policy", "垂直滚动条", "as_needed", (("as_needed", "需要时显示"), ("always", "始终显示"), ("never", "隐藏"))),
    ), container=True)
    add("splitter", "分隔容器", "容器组件", (420, 260), (
        orientation, P("handle_width", "分隔条宽度", "容器", "int", 6, minimum=1, maximum=30),
        P("children_collapsible", "允许折叠子项", "容器", "bool", False),
        P("sizes", "初始分区尺寸", "容器", "string_list", (),
          description="按对象顺序填写正整数像素；留空时均分，运行时可拖动分隔条。"),
    ), container=True, events=(("splitterMoved", "分隔条移动"),))
    for key, label in (("stacked_widget", "堆叠容器"), ("tool_box", "折叠页容器")):
        add(key, label, "容器组件", (360, 260), (
            P("current_index", "当前页面", "页面", "int", 0, maximum=49),
        ), container=True, events=(("currentChanged", "页面改变"),))
    add("mdi_area", "多文档区域", "容器组件", (560, 380), (
        enum("view_mode", "显示方式", "subwindows", (("subwindows", "子窗口"), ("tabs", "标签页"))),
        enum("arrangement", "初始排列", "manual", (("manual", "设计位置"), ("tile", "平铺"), ("cascade", "层叠"))),
    ), container=True, events=(("subWindowActivated", "子窗口激活"),))
    add("wizard_page", "向导页面", "容器组件", (360, 240), (
        title, P("subtitle", "副标题", "基本", "string", ""),
        P("complete", "允许进入下一页", "行为", "bool", True),
    ), container=True, slot="pages", events=(("completeChanged", "完成状态改变"),))
    window_props = (title, trigger, P("show_on_start", "运行时自动显示", "窗口", "bool", False))
    add("dialog", "对话框窗口", "窗口组件", (380, 280), window_props + (
        P("modal", "模态窗口", "窗口", "bool", False),),
        container=True, events=(("accepted", "被确认"), ("rejected", "被取消"), ("finished", "被关闭")))
    add("dock_widget", "停靠窗口", "窗口组件", (280, 220), (
        title, enum("dock_area", "停靠位置", "left", (("left", "左侧"), ("right", "右侧"), ("top", "顶部"), ("bottom", "底部"))),
        P("floating", "初始浮动", "窗口", "bool", False),
        P("closable", "允许关闭", "窗口", "bool", True),
        P("movable", "允许移动", "窗口", "bool", True),
        P("floatable", "允许浮动", "窗口", "bool", True),
        P("dock_width", "初始宽度", "窗口", "int", 280, minimum=80, maximum=16384),
        P("dock_height", "初始高度", "窗口", "int", 220, minimum=60, maximum=16384),
    ), container=True, slot="dock", events=(("topLevelChanged", "浮动状态改变"), ("visibilityChanged", "显示状态改变")))
    add("mdi_subwindow", "多文档子窗口", "窗口组件", (300, 220), (
        title, P("maximized", "初始最大化", "窗口", "bool", False),
    ), container=True, events=(("windowStateChanged", "窗口状态改变"),))
    add("wizard", "向导窗口", "窗口组件", (480, 360), window_props + (
        P("current_index", "起始页面", "页面", "int", 0, maximum=49),
        enum("wizard_style", "向导样式", "modern", (("modern", "现代"), ("classic", "经典"), ("mac", "简洁"))),
    ), container=True, events=(("currentIdChanged", "页面改变"), ("accepted", "完成"), ("rejected", "取消")))
    add("splash_screen", "启动画面", "窗口组件", (480, 280), (
        P("image", "背景图片", "内容", "image", ""),
        P("text", "提示文本", "内容", "string", "正在启动…"),
        P("text_color", "提示颜色", "外观", "color", "#ffffff"),
        P("duration", "显示时长毫秒", "行为", "int", 2000, minimum=0, maximum=600000),
        P("show_on_start", "运行时自动显示", "窗口", "bool", True),
        trigger,
    ), events=(("messageChanged", "提示改变"),))
    add("tab_bar", "独立选项卡栏", "容器组件", (360, 32), (
        P("items", "页签标题", "内容", "string_list", ("第一页", "第二页")),
        P("current_index", "当前页签", "内容", "int", 0, minimum=-1, maximum=999),
        P("tabs_closable", "显示关闭按钮", "行为", "bool", False),
        P("movable", "允许拖动排序", "行为", "bool", False),
        P("expanding", "均分可用宽度", "外观", "bool", True),
    ), events=(("currentChanged", "页签改变"), ("tabCloseRequested", "请求关闭"), ("tabMoved", "页签移动")))
    dialog_base = (P("title", "标题", "对话框", "string", "提示"), trigger)
    for key, label in (("message_box", "消息框"), ("error_message", "错误消息框"),
                       ("input_dialog", "输入对话框"), ("color_dialog", "颜色对话框"),
                       ("font_dialog", "字体对话框"), ("progress_dialog", "进度对话框")):
        props = dialog_base
        if key in {"message_box", "error_message", "progress_dialog"}:
            props += (P("text", "提示内容", "对话框", "multiline", "请确认操作。" if key != "progress_dialog" else "正在处理…"),)
        if key == "message_box":
            props += (enum("icon_kind", "消息类型", "information", (("information", "信息"), ("warning", "警告"), ("critical", "错误"), ("question", "询问")), "对话框"),
                      P("buttons", "按钮", "对话框", "string_list", ("确定", "取消"),
                        description="支持：确定、取消、是、否、应用、关闭、重试。"))
        if key == "input_dialog":
            props += (P("label", "输入提示", "对话框", "string", "请输入内容"),
                      enum("input_mode", "输入类型", "text", (("text", "文本"), ("integer", "整数"), ("decimal", "小数")), "对话框"),
                      P("text_value", "初始文本", "对话框", "string", ""),
                      P("minimum", "最小值", "数值", "float", 0.0, minimum=-1e9, maximum=1e9),
                      P("maximum", "最大值", "数值", "float", 100.0, minimum=-1e9, maximum=1e9),
                      P("value", "初始数值", "数值", "float", 0.0, minimum=-1e9, maximum=1e9),
                      P("decimals", "小数位数", "数值", "int", 2, maximum=6),
                      P("password", "密码输入", "对话框", "bool", False))
        if key == "color_dialog":
            props += (P("initial_color", "初始颜色", "对话框", "color", "#ffffff"),
                      P("alpha_channel", "允许透明通道", "对话框", "bool", False))
        if key == "font_dialog":
            props += (P("font_family", "初始字体", "对话框", "string", ""),
                      P("font_size", "初始字号", "对话框", "int", 10, minimum=1, maximum=96))
        if key == "progress_dialog":
            props += (P("minimum", "最小值", "数值", "int", 0, maximum=1e9),
                      P("maximum", "最大值", "数值", "int", 100, maximum=1e9),
                      P("value", "初始进度", "数值", "int", 0, maximum=1e9),
                      P("cancel_text", "取消按钮", "对话框", "string", "取消"),
                      P("auto_close", "完成后关闭", "对话框", "bool", True))
        add(key, label, "对话框组件", (176, 36), props, slot="non_visual",
            events=(("accepted", "确认并返回结果"), ("cancelled", "被取消")))
    views = (
        P("editable", "允许编辑", "行为", "bool", False),
        enum("selection_mode", "选择方式", "single", (("single", "单选"), ("extended", "扩展多选"), ("none", "不可选择"))),
        P("alternating", "交替行底色", "外观", "bool", True),
    )
    for key, label in (("list_view", "列表模型视图"), ("table_view", "表格模型视图"),
                       ("tree_view", "树形模型视图"), ("column_view", "分栏视图")):
        data = ((P("items", "列表项目", "内容", "string_list", ("项目一", "项目二")),) if key == "list_view" else
                (P("table_data", "表格内容", "内容", "table", {"headers": ("名称", "状态"), "rows": (("项目一", "就绪"),)}),) if key == "table_view" else
                (P("tree_data", "节点内容", "内容", "tree", ({"text": "根节点", "children": ({"text": "子节点", "children": ()},)},)),))
        extras = (P("sorting", "允许排序", "行为", "bool", False),) if key in {"table_view", "tree_view"} else ()
        if key == "list_view":
            extras += (enum("view_mode", "显示方式", "list", (("list", "列表"), ("icons", "图标网格")), "外观"),)
        add(key, label, "数据视图", (360, 240), data + views + extras,
            events=(("clicked", "项目被单击"), ("doubleClicked", "项目被双击"), ("activated", "项目被激活")))
    add("undo_view", "撤销历史视图", "数据视图", (220, 220), (
        P("empty_label", "初始状态文字", "内容", "string", "初始状态"),
        P("clean_icon", "已保存图标", "内容", "image", ""),
    ), events=(("clicked", "历史项被单击"),))
    add("dialog_button_box", "对话框按钮组", "按钮组件", (300, 36), (
        P("buttons", "按钮", "内容", "string_list", ("确定", "取消")), orientation,
        P("center_buttons", "按钮居中", "外观", "bool", False),
        P("close_parent_dialog", "确认取消控制所属对话框", "行为", "bool", True),
    ), events=(("accepted", "被确认"), ("rejected", "被取消"), ("clicked", "按钮被单击"), ("helpRequested", "请求帮助")))
    add("button_group", "非可视按钮组", "非可视组件", (176, 36), (
        P("members", "成员代码名称", "内容", "string_list", (), description="填写按钮、选择框或单选框的代码名称；每个按钮只能属于一个显式按钮组。"),
        P("exclusive", "组内互斥", "行为", "bool", True),
    ), slot="non_visual", events=(("idClicked", "成员被单击"), ("idToggled", "成员选中状态改变")))
    add("graphics_view", "图形视图", "图形组件", (360, 260), (
        P("scene_width", "场景宽度", "内容", "int", 640, minimum=1, maximum=16384),
        P("scene_height", "场景高度", "内容", "int", 480, minimum=1, maximum=16384),
        P("image", "场景图片", "内容", "image", ""),
        P("text", "场景文字", "内容", "multiline", "图形场景"),
        P("zoom", "缩放百分比", "外观", "int", 100, minimum=10, maximum=400),
        P("interactive", "允许场景交互", "行为", "bool", True),
    ))
    for key, label in (("rhi_widget", "硬件渲染控件"), ("opengl_widget", "OpenGL 绘图控件")):
        add(key, label, "图形组件", (360, 240), (
            P("clear_color", "清屏颜色", "绘图", "color", "#203044"),
            P("samples", "多重采样", "绘图", "int", 1, minimum=1, maximum=8),
        ), events=(("initialized", "图形上下文就绪"), ("rendered", "绘制完成"), ("failed", "图形初始化失败")))
    add("svg_widget", "SVG 矢量图", "图形组件", (200, 160), (
        P("svg_data", "SVG 内容", "内容", "multiline",
          '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="160" viewBox="0 0 200 160"><rect x="20" y="20" width="160" height="120" rx="16" fill="#0078d4"/></svg>',
          description="点击图标按钮，按分类或中英文搜索常用图标，设置颜色和线宽；也可编辑 SVG 源码。内容随项目保存，预览与导出均生效。"),
    ))
    add("web_view", "网页控件", "扩展组件", (480, 320), (
        enum("source_mode", "页面来源", "html", (("html", "内嵌 HTML"), ("url", "网址")), "内容"),
        P("html", "HTML 内容", "内容", "multiline", "<!doctype html><meta charset='utf-8'><h1>网页控件</h1><p>在预览中运行网页。</p>"),
        P("url", "页面网址", "内容", "string", "about:blank"),
        P("javascript", "允许 JavaScript", "行为", "bool", True),
        P("zoom_factor", "页面缩放", "外观", "float", 1.0, minimum=0.25, maximum=5.0),
    ), events=(("loadStarted", "开始加载"), ("loadProgress", "加载进度"), ("loadFinished", "加载完成"), ("urlChanged", "网址改变"), ("titleChanged", "标题改变")))
