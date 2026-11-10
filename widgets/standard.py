"""输入、选择与数据展示组件的中文元数据。"""

from __future__ import annotations

from core.metadata import PropertySpec as P, WidgetSpec
from core.registry import WidgetRegistry


ALIGNMENT = (("left_vcenter", "靠左"), ("center", "居中"), ("right_vcenter", "靠右"))
ORIENTATION = (("horizontal", "横向"), ("vertical", "纵向"))
SELECTION = (("single", "单选"), ("extended", "扩展多选"), ("multi", "点击多选"), ("none", "不可选择"))
FRAME = (("none", "无边框"), ("box", "方框"), ("panel", "面板"), ("styled", "系统面板"))


def register_standard_widgets(registry: WidgetRegistry, common: tuple[P, ...]) -> None:
    def register(key: str, label: str, group: str, qt_class: str, size: tuple[int, int],
                 properties: tuple[P, ...], *, named: bool = False) -> None:
        registry.register(WidgetSpec("builtin." + key, label, group, qt_class, 1, "children", size, key,
                                     properties + common, text_from_name=named))

    register("text_edit", "多行编辑框", "输入组件", "QPlainTextEdit", (280, 144), (
        P("text", "文本", "内容", "multiline", "", "plainText"),
        P("placeholder_text", "占位文本", "基本", "string", "请输入多行内容", "placeholderText"),
        P("read_only", "只读", "行为", "bool", False, "readOnly"),
        P("line_wrap", "自动换行", "行为", "enum", "widget", "lineWrapMode", (("widget", "按宽度换行"), ("none", "不自动换行"))),
        P("tab_changes_focus", "制表键切换焦点", "行为", "bool", False, "tabChangesFocus"),
        P("undo_enabled", "允许撤销输入", "行为", "bool", True, "undoRedoEnabled"),
        P("frame_shape", "边框样式", "外观", "enum", "styled", "frameShape", FRAME),
    ))
    register("combo_box", "组合框", "选择组件", "QComboBox", (180, 32), (
        P("items", "列表项目", "内容", "string_list", ("选项一", "选项二", "选项三")),
        P("current_index", "当前选项", "内容", "int", 0, minimum=-1, maximum=999,
          description="从零开始计数；负一表示不选择。删除项目时自动调整到有效选项。"),
        P("editable", "允许输入", "行为", "bool", False, "editable"),
        P("placeholder_text", "占位文本", "基本", "string", "请选择", "placeholderText"),
        P("max_visible_items", "下拉显示项数", "外观", "int", 10, "maxVisibleItems", minimum=1, maximum=100),
        P("insert_policy", "输入添加方式", "行为", "enum", "none", "insertPolicy", (
            ("none", "不添加新项目"), ("bottom", "添加到末尾"), ("top", "添加到开头"))),
        P("duplicates_enabled", "允许重复项目", "行为", "bool", False, "duplicatesEnabled"),
    ))
    register("check_box", "选择框", "选择组件", "QCheckBox", (136, 32), (
        P("text", "标题", "基本", "string", "选择框", "text"),
        P("tristate", "允许半选", "行为", "bool", False, "tristate"),
        P("check_state", "选中状态", "基本", "enum", "unchecked", options=(
            ("unchecked", "未选中"), ("checked", "已选中"), ("partial", "半选"))),
    ), named=True)
    register("radio_button", "单选框", "选择组件", "QRadioButton", (136, 32), (
        P("text", "标题", "基本", "string", "单选框", "text"),
        P("auto_exclusive", "同容器互斥", "行为", "bool", True, "autoExclusive",
          description="选中一个单选框，会取消同一容器内其他互斥单选框的选中状态；整次修改可撤销。"),
        P("checked", "已选中", "基本", "bool", False, "checked"),
    ), named=True)
    numeric = (
        P("minimum", "最小值", "数值", "int", 0, minimum=-1000000000, maximum=1000000000,
          description="不能大于最大值；缩小范围时当前值随之调整，整次修改可撤销。"),
        P("maximum", "最大值", "数值", "int", 100, minimum=-1000000000, maximum=1000000000,
          description="不能小于最小值；缩小范围时当前值随之调整，整次修改可撤销。"),
        P("value", "当前值", "数值", "int", 0, minimum=-1000000000, maximum=1000000000),
    )
    register("spin_box", "数值输入框", "输入组件", "QSpinBox", (144, 32), numeric + (
        P("single_step", "步长", "数值", "int", 1, "singleStep", minimum=1, maximum=1000000),
        P("prefix", "数值前缀", "外观", "string", "", "prefix"),
        P("suffix", "数值后缀", "外观", "string", "", "suffix"),
        P("special_value_text", "最小值替代文字", "外观", "string", "", "specialValueText"),
        P("wrapping", "首尾循环", "行为", "bool", False, "wrapping"),
        P("read_only", "只读", "行为", "bool", False, "readOnly"),
        P("alignment", "对齐方式", "外观", "enum", "left_vcenter", "alignment", ALIGNMENT),
        P("button_symbols", "调节按钮", "外观", "enum", "arrows", "buttonSymbols", (
            ("arrows", "上下箭头"), ("plus_minus", "加减符号"), ("none", "隐藏按钮"))),
    ))
    register("progress_bar", "进度条", "显示组件", "QProgressBar", (240, 28), numeric + (
        P("format", "显示格式", "外观", "string", "%p%", "format", description="百分比使用 %p，当前值使用 %v，总步数使用 %m。"),
        P("text_visible", "显示文字", "外观", "bool", True, "textVisible"),
        P("orientation", "方向", "外观", "enum", "horizontal", "orientation", ORIENTATION),
        P("inverted", "反向显示", "外观", "bool", False, "invertedAppearance"),
        P("alignment", "对齐方式", "外观", "enum", "center", "alignment", ALIGNMENT),
    ))
    register("slider", "滑块", "输入组件", "QSlider", (240, 32), numeric + (
        P("single_step", "步长", "数值", "int", 1, "singleStep", minimum=1, maximum=1000000),
        P("page_step", "翻页步长", "数值", "int", 10, "pageStep", minimum=1, maximum=1000000),
        P("orientation", "方向", "外观", "enum", "horizontal", "orientation", ORIENTATION),
        P("tick_position", "刻度位置", "外观", "enum", "none", "tickPosition", (
            ("none", "无刻度"), ("above", "上方或左侧"), ("below", "下方或右侧"), ("both", "两侧"))),
        P("tick_interval", "刻度间隔", "外观", "int", 0, "tickInterval", maximum=1000000, description="零表示自动间隔。"),
        P("tracking", "拖动时实时更新", "行为", "bool", True, "tracking"),
        P("inverted", "反向显示", "外观", "bool", False, "invertedAppearance"),
    ))
    item_view = (
        P("alternating_rows", "交替行底色", "外观", "bool", True, "alternatingRowColors"),
        P("selection_mode", "选择方式", "行为", "enum", "single", "selectionMode", SELECTION),
        P("edit_triggers", "编辑方式", "行为", "enum", "none", "editTriggers", (
            ("none", "禁止编辑"), ("double_click", "双击编辑"), ("all", "直接编辑"))),
        P("frame_shape", "边框样式", "外观", "enum", "styled", "frameShape", FRAME),
    )
    register("list_widget", "列表框", "数据组件", "QListWidget", (220, 160), (
        P("items", "列表项目", "内容", "string_list", ("项目一", "项目二", "项目三")),
        P("current_index", "当前选项", "内容", "int", -1, minimum=-1, maximum=999,
          description="从零开始计数；负一表示不选择。"),
        P("spacing", "项目间距", "外观", "int", 0, "spacing", maximum=100),
        P("word_wrap", "自动换行", "外观", "bool", False, "wordWrap"),
    ) + item_view)
    register("table_widget", "表格", "数据组件", "QTableWidget", (360, 192), (
        P("table_data", "表格内容", "内容", "table", {"headers": ("名称", "说明"), "rows": (("项目一", "说明一"), ("项目二", "说明二"))},
          description="编辑行、列标题和各列宽度；可输入精确宽度或拖动列标题边界。"),
        P("show_grid", "显示网格线", "外观", "bool", True, "showGrid"),
        P("show_horizontal_header", "显示列标题", "外观", "bool", True),
        P("show_vertical_header", "显示行号", "外观", "bool", True),
        P("column_width", "默认列宽", "外观", "int", 100, minimum=24, maximum=2000,
          description="只影响尚未自定义宽度的列；各列宽度在“表格内容”中设置。"),
        P("stretch_last_section", "末列填满", "外观", "bool", True,
          description="末列未自定义宽度时填满剩余空间；设置了明确宽度后以列宽为准。"),
        P("selection_behavior", "选择范围", "行为", "enum", "rows", "selectionBehavior", (
            ("items", "单元格"), ("rows", "整行"), ("columns", "整列"))),
        P("word_wrap", "自动换行", "外观", "bool", True, "wordWrap"),
    ) + item_view)
    register("tree_widget", "树形框", "数据组件", "QTreeWidget", (240, 192), (
        P("tree_data", "树形内容", "内容", "tree", ({"text": "分组一", "children": ({"text": "项目一", "children": ()},)},)),
        P("header_text", "列标题", "内容", "string", "名称"),
        P("header_hidden", "隐藏列标题", "外观", "bool", False, "headerHidden"),
        P("root_decorated", "显示根展开按钮", "外观", "bool", True, "rootIsDecorated"),
        P("items_expandable", "允许展开", "行为", "bool", True, "itemsExpandable"),
        P("expanded", "默认全部展开", "行为", "bool", True),
        P("indentation", "层级缩进", "外观", "int", 20, "indentation", maximum=100),
    ) + item_view)
