"""富文本、字体和快捷键输入，以及已有组件的补充属性。"""

from dataclasses import replace

from core.metadata import PropertySpec as P, WidgetSpec


BUTTON_CLASSES = {"QPushButton", "QToolButton", "QCommandLinkButton", "QCheckBox", "QRadioButton"}
TEXT_FORMATS = (("plain", "纯文本"), ("rich", "富文本 HTML"))


def register_input_extras(registry, common):
    def add(key, label, cls, size, properties):
        registry.register(WidgetSpec("builtin." + key, label, "输入组件", cls, 1, "children", size, key,
                                     properties + common))

    text = (
        P("text", "初始内容", "内容", "multiline", ""),
        P("text_format", "内容格式", "内容", "enum", "plain", options=TEXT_FORMATS,
          description="纯文本原样显示；富文本按 Qt 支持的 HTML 格式显示。"),
        P("read_only", "只读", "行为", "bool", False, "readOnly"),
        P("placeholder_text", "占位文本", "基本", "string", "", "placeholderText"),
        P("rich_line_wrap", "自动换行", "行为", "enum", "widget", "lineWrapMode",
          (("none", "不自动换行"), ("widget", "按宽度换行"))),
        P("tab_changes_focus", "制表键切换焦点", "行为", "bool", False, "tabChangesFocus"),
        P("tab_stop_distance", "制表符宽度", "外观", "int", 80, "tabStopDistance", minimum=4, maximum=500),
        P("cursor_width", "光标宽度", "外观", "int", 1, "cursorWidth", minimum=1, maximum=20),
        P("undo_enabled", "允许撤销输入", "行为", "bool", True, "undoRedoEnabled"),
        P("accept_rich_text", "允许粘贴富文本", "行为", "bool", True, "acceptRichText"),
        P("document_margin", "文档边距", "外观", "int", 4, minimum=0, maximum=100),
    )
    add("rich_text_edit", "富文本编辑框", "QTextEdit", (300, 180), text)
    browser = tuple(replace(prop, default=True) if prop.key == "read_only" else
                    replace(prop, default="rich") if prop.key == "text_format" else prop for prop in text)
    add("text_browser", "文本浏览器", "QTextBrowser", (320, 200), browser + (
        P("open_links", "自动跟随链接", "行为", "bool", True, "openLinks",
          description="关闭后仅触发链接事件，由业务处理跳转；页内锚点可用于帮助文档。"),
        P("open_external_links", "使用外部程序打开链接", "行为", "bool", False, "openExternalLinks"),
    ))
    add("font_combo_box", "字体组合框", "QFontComboBox", (220, 32), (
        P("current_font", "当前字体", "内容", "string", "",
          description="从本机字体选择；留空使用应用默认字体，缺失字体由系统回退。"),
        P("font_filter", "字体范围", "内容", "enum", "all", "fontFilters", (
            ("all", "全部字体"), ("scalable", "可缩放字体"), ("non_scalable", "点阵字体"),
            ("monospace", "等宽字体"), ("proportional", "非等宽字体"))),
        P("writing_system", "文字系统", "内容", "enum", "any", "writingSystem", (
            ("any", "全部"), ("latin", "拉丁文字"), ("simplified_chinese", "简体中文"),
            ("traditional_chinese", "繁体中文"), ("japanese", "日文"), ("korean", "韩文"))),
        P("editable", "允许输入", "行为", "bool", True, "editable"),
        P("max_visible_items", "下拉显示项数", "外观", "int", 10, "maxVisibleItems", minimum=1, maximum=100),
    ))
    add("key_sequence_edit", "快捷键编辑框", "QKeySequenceEdit", (220, 32), (
        P("key_sequence", "当前快捷键", "内容", "shortcut", "",
          description="运行时按键录入单组组合键；此组件只录入快捷键，不会自动执行菜单或按钮。"),
        P("clear_button", "清除按钮", "行为", "bool", True, "clearButtonEnabled"),
    ))


def extend_properties(spec):
    additions = []
    cls = spec.qt_class
    if cls in {"QPushButton", "QToolButton", "QCommandLinkButton"}:
        additions.extend((
            P("navigation_page", "关联页面", "导航", "string", "",
              description="点击后切换到指定页面；支持选择夹、堆叠窗口和工具箱。预览和导出均生效。"),
            P("navigation_style", "导航样式", "导航", "enum", "default",
              options=(("default", "默认"), ("sidebar", "侧栏导航（透明底）")),
              description="侧栏样式提供悬停、按下和当前页面高亮；文字与图标可直接设置在按钮上。"),
        ))
    if cls in BUTTON_CLASSES | {"QAction"}:
        additions.append(P("icon", "图标", "外观", "image", "",
                           description="选择图片或图标，随项目保存并随代码导出；清除后恢复组件默认图标。"))
    if cls in BUTTON_CLASSES:
        additions.extend((
            P("icon_width", "图标宽度", "外观", "int", 0, maximum=256, description="零表示组件默认图标宽度。"),
            P("icon_height", "图标高度", "外观", "int", 0, maximum=256, description="零表示组件默认图标高度。"),
            P("shortcut", "快捷键", "行为", "shortcut", "", description="窗口内触发按钮的快捷键；不能与其他按钮或菜单重复。"),
        ))
    if cls in {"QToolButton", "QCommandLinkButton", "QCheckBox", "QRadioButton"}:
        additions.extend((
            P("auto_repeat", "长按重复触发", "行为", "bool", False, "autoRepeat"),
            P("repeat_delay", "首次重复延时", "行为", "int", 300, "autoRepeatDelay", maximum=60000),
            P("repeat_interval", "重复间隔", "行为", "int", 100, "autoRepeatInterval", minimum=1, maximum=60000),
        ))
    if cls == "QAction":
        additions.append(P("tool_tip", "提示文本", "行为", "string", "", "toolTip"))
    if cls == "QLabel":
        additions.extend((
            P("text_format", "文本格式", "内容", "enum", "plain", "textFormat", TEXT_FORMATS),
            P("text_interaction", "文本交互", "行为", "enum", "links", "textInteractionFlags", (
                ("none", "不可交互"), ("select", "允许选中文字"), ("links", "允许点击链接"),
                ("select_links", "选择文字并点击链接"))),
            P("open_external_links", "使用外部程序打开链接", "行为", "bool", False, "openExternalLinks"),
        ))
    if cls == "QGroupBox":
        additions.extend((P("checkable", "显示选择框", "行为", "bool", False, "checkable"),
                          P("checked", "已选中", "行为", "bool", False,
                            description="取消选中时禁用组内控件；重新选中后恢复。")))
    if cls in {"QSpinBox", "QDoubleSpinBox", "QDateEdit", "QTimeEdit", "QDateTimeEdit"}:
        additions.extend((P("keyboard_tracking", "输入时实时更新", "行为", "bool", True, "keyboardTracking"),
                          P("frame", "显示边框", "外观", "bool", True, "frame"),
                          P("accelerated", "长按加速", "行为", "bool", False, "accelerated")))
    if cls in {"QDoubleSpinBox", "QDateEdit", "QTimeEdit", "QDateTimeEdit"}:
        additions.append(P("button_symbols", "调节按钮", "外观", "enum", "arrows", "buttonSymbols", (
            ("arrows", "上下箭头"), ("plus_minus", "加减符号"), ("none", "隐藏按钮"))))
    if cls == "QDoubleSpinBox":
        additions.append(P("special_value_text", "最小值替代文字", "外观", "string", "", "specialValueText"))
    if cls in {"QSlider", "QDial", "QScrollBar"}:
        additions.append(P("inverted_controls", "反向操作", "行为", "bool", cls == "QScrollBar", "invertedControls"))
    if cls == "QPlainTextEdit":
        additions.extend((P("tab_stop_distance", "制表符宽度", "外观", "int", 80, "tabStopDistance", minimum=4, maximum=500),
                          P("cursor_width", "光标宽度", "外观", "int", 1, "cursorWidth", minimum=1, maximum=20),
                          P("center_on_scroll", "滚动时居中光标", "行为", "bool", False, "centerOnScroll")))
    return replace(spec, properties=spec.properties + tuple(additions))
