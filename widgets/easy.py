"""面向易语言使用习惯的基础组件，注册真实能力及中文名称。"""

from __future__ import annotations

from core.metadata import EventSpec as E, PropertySpec as P, WidgetSpec
from core.registry import WidgetRegistry


def register_easy_widgets(registry: WidgetRegistry, common: tuple[P, ...]) -> None:
    def add(key: str, label: str, cls: str, size: tuple[int, int], properties: tuple[P, ...], *,
            slot: str = "children", group: str = "易语言基础", contain: bool = False,
            toolbox: bool = True, events: tuple[E, ...] = ()) -> None:
        visual = slot != "non_visual"
        registry.register(WidgetSpec("builtin." + key, label, group, cls, 1, slot, size, key,
                          properties + (common if visual else ()), toolbox=toolbox, can_contain=contain, events=events))

    add("drawing_board", "画板", "DrawingBoard", (320, 220), (
        P("pen_color", "画笔颜色", "绘图", "color", "#20252b"),
        P("pen_width", "画笔宽度", "绘图", "int", 2, minimum=1, maximum=30),
        P("paper_color", "画板底色", "绘图", "color", "#ffffff"),
        P("drawing_enabled", "允许鼠标绘画", "行为", "bool", True),
        P("image", "底图", "内容", "image", ""),
    ), events=(E("pressed", "画笔按下", "pressed"), E("released", "画笔放开", "released"), E("changed", "内容改变", "changed")))
    add("picture_box", "图片框", "PictureBox", (240, 180), (
        P("image", "图片", "内容", "image", ""),
        P("image_mode", "显示方式", "外观", "enum", "fit", options=(("fit", "等比缩放"), ("stretch", "拉伸"), ("center", "居中原图"))),
        P("border", "显示边框", "外观", "bool", True),
    ), events=(E("clicked", "被单击", "clicked"), E("double_clicked", "被双击", "doubleClicked")))
    add("tab_widget", "选择夹", "SelectionTabs", (420, 300), (
        P("current_index", "当前页", "页面", "int", 0, maximum=49,
          description="从零开始计数；也可直接单击画布上的页标题切换。右键可添加或删除页面。"),
        P("tab_position", "表头朝向", "表头", "enum", "top", options=(
            ("top", "顶部"), ("bottom", "底部"), ("left", "左侧"), ("right", "右侧")),
          description="页签栏所在位置；左右朝向会旋转页签文字。"),
        P("header_visible", "显示表头", "表头", "bool", True,
          description="关闭后隐藏整个页签栏并释放内容空间。仍可通过当前页属性、对象树或运行代码切换页面。"),
        P("tab_bar_auto_hide", "单页自动隐藏表头", "表头", "bool", False),
        P("tab_bar_size", "表头厚度", "表头", "int", 30, minimum=18, maximum=200,
          description="上下表头的高度，或左右表头的宽度，单位为逻辑像素。字号或图标较大时可相应增加。"),
        P("tab_shape", "页签形状", "表头", "enum", "rounded", options=(("rounded", "圆角"), ("triangular", "三角"))),
        P("expanding", "页签均分表头", "表头", "bool", False),
        P("uses_scroll_buttons", "显示页签滚动按钮", "表头", "bool", True),
        P("elide_mode", "长标题省略方式", "表头", "enum", "right", options=(
            ("none", "不省略"), ("left", "省略开头"), ("middle", "省略中间"), ("right", "省略末尾"))),
        P("document_mode", "文档模式", "表头", "bool", False),
        P("draw_base", "绘制表头基线", "表头", "bool", True),
        P("pane_border", "显示页面边框", "外观", "bool", True),
        P("movable", "允许拖动页签排序", "行为", "bool", False,
          description="预览和运行时可拖动页签；页面内容随页签一起排序，不回写设计文件。设计顺序通过对象树调整。"),
        P("tabs_closable", "显示页签关闭按钮", "行为", "bool", False,
          description="点击后触发页签关闭请求；业务代码决定是否关闭，不会自动删除页面内容。"),
        P("icon_width", "页签图标宽度", "表头", "int", 16, minimum=1, maximum=128),
        P("icon_height", "页签图标高度", "表头", "int", 16, minimum=1, maximum=128),
    ), contain=True, events=(E("current_changed", "选择改变", "currentChanged"),))
    add("tab_page", "选择夹页面", "QWidget", (418, 269), (
        P("text", "页标题", "页面", "string", "页面"),
        P("tab_icon", "页签图标", "页面", "image", "", description="用于所属选择夹的页签；页签悬停提示使用本页的提示文本属性。"),),
        slot="pages", contain=True, toolbox=False)
    add("timer", "时钟", "QTimer", (152, 36), (
        P("interval", "时钟周期", "时钟", "int", 1000, minimum=1, maximum=86400000,
          description="单位为毫秒。设计时不运行，预览和导出运行时按启用状态启动。"),
        P("enabled", "启用", "时钟", "bool", True),
        P("auto_start", "自动启动", "时钟", "bool", True,
          description="运行时自动开始计时；关闭后可在业务代码中调用 start()。"),
        P("single_shot", "只触发一次", "时钟", "bool", False),
    ), slot="non_visual", events=(E("timeout", "周期事件", "timeout"),))
    add("common_dialog", "通用对话框", "CommonDialog", (168, 36), (
        P("dialog_kind", "对话框类型", "对话框", "enum", "open_file", options=(
            ("open_file", "打开文件"), ("open_files", "打开多个文件"), ("save_file", "保存文件"),
            ("directory", "选择文件夹"), ("color", "选择颜色"), ("font", "选择字体"))),
        P("title", "标题", "对话框", "string", "请选择"),
        P("filter", "文件过滤器", "对话框", "string", "所有文件 (*)"),
        P("initial_directory", "初始目录", "对话框", "string", ""),
        P("default_suffix", "默认扩展名", "对话框", "string", ""),
        P("trigger_control", "触发按钮", "行为", "string", "",
          description="选择按钮后，预览和导出程序点击该按钮即可打开。也可在业务代码中调用 open_dialog()。"),
    ), slot="non_visual", events=(E("accepted", "选择完成", "accepted"), E("cancelled", "被取消", "cancelled")))
    add("super_list", "超级列表框", "SuperList", (400, 240), (
        P("table_data", "表项与列", "内容", "table", {"headers": ["名称", "状态", "说明"], "rows": [["项目一", "待处理", "双击可触发事件"]]},
          description="编辑行、列标题和各列宽度；例如将 ID 列设窄，说明列设宽。"),
        P("checkboxes", "显示选择框", "行为", "bool", False),
        P("checked_rows", "已勾选行", "内容", "string_list", (), description="填写从一开始的行号，每行一个。"),
        P("multi_select", "允许多选", "行为", "bool", False),
        P("full_row", "整行选择", "行为", "bool", True),
        P("editable", "允许编辑", "行为", "bool", False),
        P("sorting", "允许列排序", "行为", "bool", False),
        P("alternating", "交替行颜色", "外观", "bool", True),
        P("header_visible", "显示列标题", "外观", "bool", True),
        P("column_width", "默认列宽", "外观", "int", 120, minimum=24, maximum=2000,
          description="只影响尚未自定义宽度的列；各列宽度在“表项与列”中设置。"),
        P("stretch_last_section", "末列填满", "外观", "bool", True,
          description="末列未自定义宽度时填满剩余空间；设置了明确宽度后以列宽为准。"),
        P("row_height", "行高", "外观", "int", 26, minimum=18, maximum=96),
    ), events=(E("clicked", "表项被单击", "itemClicked"), E("double_clicked", "表项被双击", "itemDoubleClicked"),
               E("selection_changed", "选择改变", "itemSelectionChanged"), E("item_changed", "表项改变", "itemChanged")))
    add("tool_bar", "工具条", "QToolBar", (320, 36), (
        P("items", "按钮列表", "内容", "string_list", ("新建", "打开", "保存"), description="每行一个按钮；单独的减号表示分隔线。"),
        P("bar_height", "高度", "外观", "int", 36, minimum=28, maximum=96),
    ), slot="tool_bar", events=(E("triggered", "按钮被单击", "actionTriggered"),))
    add("status_bar", "状态条", "QStatusBar", (320, 28), (
        P("text", "文本", "基本", "string", "就绪"),
        P("panels", "状态栏列表", "内容", "string_list", ()),
        P("bar_height", "高度", "外观", "int", 28, minimum=22, maximum=96),
        P("size_grip", "显示尺寸手柄", "行为", "bool", True),
    ), slot="status_bar", events=(E("message_changed", "文本改变", "messageChanged"),))
