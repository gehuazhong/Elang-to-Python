"""补齐适合持久化设计的常用属性，保留已有字段与默认行为。"""

from dataclasses import replace

from core.metadata import PropertySpec as P


ALIGNMENT = (("left_vcenter", "靠左"), ("center", "居中"), ("right_vcenter", "靠右"),
             ("top_left", "左上"), ("top_center", "顶部居中"), ("top_right", "右上"),
             ("bottom_left", "左下"), ("bottom_center", "底部居中"), ("bottom_right", "右下"))
SCROLL = (("as_needed", "按需显示"), ("always", "始终显示"), ("never", "始终隐藏"))
ELIDE = (("none", "不省略"), ("left", "省略开头"), ("middle", "省略中间"), ("right", "省略末尾"))
POSITIONS = (("top", "顶部"), ("bottom", "底部"), ("left", "左侧"), ("right", "右侧"))
SHAPES = (("rounded", "圆角"), ("triangular", "三角"))
RESIZE = (("interactive", "手动调整"), ("fixed", "固定宽度"), ("stretch", "填满空间"), ("contents", "适应内容"))
ITEM_VIEWS = {"QListWidget", "QTableWidget", "QTreeWidget", "SuperList", "QListView", "QTableView", "QTreeView", "QColumnView", "QUndoView"}
TREES = {"QTreeWidget", "SuperList", "QTreeView"}
TABLES = {"QTableWidget", "QTableView"}
SCROLL_AREAS = ITEM_VIEWS | {"QPlainTextEdit", "QTextEdit", "QTextBrowser", "QScrollArea", "QMdiArea", "QGraphicsView"}
FRAMES = SCROLL_AREAS | {"QLabel", "QFrame", "QLCDNumber", "QSplitter", "QStackedWidget", "QToolBox"}
LAYOUTS = {"QHBoxLayout", "QVBoxLayout", "QGridLayout", "QFormLayout"}


def flag(key, label, default=False, native=None, group="行为", description=""):
    return P(key, label, group, "bool", default, native, description=description)


def integer(key, label, default, native=None, low=0, high=10000, group="外观"):
    return P(key, label, group, "int", default, native, minimum=low, maximum=high)


def choice(key, label, default, options, native=None, group="外观"):
    return P(key, label, group, "enum", default, native, options=options)


def text(key, label, default="", native=None, group="基本", multiline=False):
    return P(key, label, group, "multiline" if multiline else "string", default, native)


def extend_properties(spec):
    cls = spec.qt_class
    extra = []
    if spec.slot not in {"non_visual", "menu"} and cls not in LAYOUTS | {"QSpacerItem"}:
        extra += [choice("cursor_shape", "鼠标指针", "default", (
            ("default", "组件默认"), ("arrow", "箭头"), ("pointing_hand", "手形"), ("ibeam", "文本光标"),
            ("cross", "十字"), ("wait", "等待"), ("forbidden", "禁止"), ("open_hand", "张开手"), ("closed_hand", "握住手"))),
            choice("focus_policy", "键盘焦点方式", "default", (("default", "组件默认"), ("none", "不接收焦点"),
                ("tab", "Tab 键"), ("click", "鼠标点击"), ("strong", "Tab 与点击"), ("wheel", "包括滚轮")), group="行为"),
            flag("mouse_tracking", "跟踪鼠标移动", False, "mouseTracking"),
            text("accessible_name", "无障碍名称", native="accessibleName", group="高级"),
            text("accessible_description", "无障碍说明", native="accessibleDescription", group="高级"),
            text("whats_this", "帮助说明", native="whatsThis", group="高级", multiline=True),
            integer("tool_tip_duration", "提示显示毫秒", -1, "toolTipDuration", -1, 600000, "行为"),
            text("style_sheet", "自定义样式", group="高级", multiline=True)]
        if spec.slot == "children":
            policies = (("default", "组件默认"), ("fixed", "固定"), ("minimum", "最小"), ("maximum", "最大"),
                        ("preferred", "首选"), ("expanding", "扩展"), ("minimum_expanding", "最小并扩展"), ("ignored", "忽略建议尺寸"))
            extra += [choice("size_policy_horizontal", "水平尺寸策略", "default", policies, group="布局"),
                      choice("size_policy_vertical", "垂直尺寸策略", "default", policies, group="布局")]
    if cls in FRAMES:
        extra += [choice("frame_shape", "边框样式", "styled" if cls in SCROLL_AREAS else "box" if cls == "QLCDNumber" else "none",
                         (("none", "无边框"), ("box", "方框"), ("panel", "面板"), ("styled", "系统面板")), "frameShape"),
                  choice("frame_shadow", "边框阴影", "sunken" if cls in SCROLL_AREAS else "raised" if cls == "QLCDNumber" else "plain",
                         (("plain", "平面"), ("raised", "凸起"), ("sunken", "凹下")), "frameShadow"),
                  integer("line_width", "边框线宽", 1, "lineWidth", high=20),
                  integer("mid_line_width", "中线宽度", 0, "midLineWidth", high=20)]
    if cls in SCROLL_AREAS:
        extra += [choice("horizontal_policy", "水平滚动条", "as_needed", SCROLL, "horizontalScrollBarPolicy"),
                  choice("vertical_policy", "垂直滚动条", "as_needed", SCROLL, "verticalScrollBarPolicy")]
    if cls in {"QPushButton", "QCommandLinkButton"}:
        extra += [flag("auto_default", "获得焦点时作为默认按钮", False, "autoDefault"),
                  flag("default_button", "默认按钮", False, "default")]
    if cls == "QLineEdit":
        extra += [text("input_mask", "输入掩码", group="内容"), flag("drag_enabled", "允许拖出选中文字", False, "dragEnabled"),
                  choice("cursor_move_style", "光标移动方式", "logical", (("logical", "逻辑顺序"), ("visual", "视觉顺序")), "cursorMoveStyle", "行为")]
    if cls in {"QComboBox", "QFontComboBox"}:
        extra += [flag("frame", "显示边框", True, "frame", "外观"),
                  integer("minimum_contents_length", "最小内容字符数", 0, "minimumContentsLength", high=1000),
                  choice("size_adjust_policy", "内容尺寸调整", "first_show", (("always", "始终适应内容"),
                         ("first_show", "首次显示时适应"), ("minimum", "按最小字符数")), "sizeAdjustPolicy"),
                  text("placeholder_text", "占位文本", native="placeholderText")]
    if cls in {"QSpinBox", "QDoubleSpinBox", "QDateEdit", "QTimeEdit", "QDateTimeEdit"}:
        extra += [flag("group_separator", "显示千位分隔符", False, "showGroupSeparator", "外观"),
                  choice("correction_mode", "无效输入修正", "previous", (("previous", "恢复上次值"), ("nearest", "使用最近有效值")), "correctionMode", "行为"),
                  choice("alignment", "文字对齐", "left_vcenter", ALIGNMENT, "alignment"),
                  text("special_value_text", "最小值替代文字", native="specialValueText", group="外观")]
    if cls in {"QSpinBox", "QDoubleSpinBox"}:
        extra.append(choice("step_type", "步进方式", "default", (("default", "固定步长"), ("adaptive", "自适应小数步长")), "stepType", "数值"))
    if cls == "QSpinBox":
        extra.append(integer("display_integer_base", "显示进制", 10, "displayIntegerBase", 2, 36, "数值"))
    if cls == "QProgressBar":
        extra.append(choice("text_direction", "竖向文字朝向", "top_to_bottom", (("top_to_bottom", "从上到下"), ("bottom_to_top", "从下到上")), "textDirection"))
    if cls == "QDial":
        extra += [flag("inverted", "反向显示", False, "invertedAppearance", "外观"),
                  P("notch_target", "刻度目标间距", "外观", "float", 3.7, "notchTarget", minimum=1, maximum=100)]
    if cls == "QCalendarWidget":
        extra += [flag("date_edit_enabled", "允许键盘输入日期", True, "dateEditEnabled"),
                  integer("date_edit_delay", "日期输入确认毫秒", 1500, "dateEditAcceptDelay", 0, 60000, "行为")]
    if cls in {"QPlainTextEdit", "QTextEdit", "QTextBrowser"}:
        extra += [flag("overwrite_mode", "覆盖输入模式", False, "overwriteMode"),
                  text("document_title", "文档标题", native="documentTitle", group="内容")]
    if cls == "QPlainTextEdit":
        extra.append(flag("background_visible", "显示文档外背景", False, "backgroundVisible", "外观"))
    if cls == "QKeySequenceEdit":
        extra.append(integer("maximum_sequence_length", "快捷键序列长度", 1, low=1, high=4, group="行为"))
    if cls == "QLCDNumber":
        extra.append(choice("number_mode", "显示进制", "decimal", (("decimal", "十进制"), ("hex", "十六进制"), ("octal", "八进制"), ("binary", "二进制")), "mode", "数值"))
    if cls in ITEM_VIEWS:
        extra += [choice("text_elide_mode", "长文本省略方式", "right", ELIDE, "textElideMode"),
                  choice("vertical_scroll_mode", "垂直滚动方式", "item", (("item", "按条目"), ("pixel", "按像素")), "verticalScrollMode"),
                  choice("horizontal_scroll_mode", "水平滚动方式", "item", (("item", "按条目"), ("pixel", "按像素")), "horizontalScrollMode"),
                  flag("auto_scroll", "拖动时自动滚动", True, "autoScroll"),
                  integer("auto_scroll_margin", "自动滚动边缘宽度", 16, "autoScrollMargin", 0, 200, "行为"),
                  flag("tab_key_navigation", "Tab 键移动条目焦点", cls in TABLES, "tabKeyNavigation"),
                  choice("drag_drop_mode", "条目拖放方式", "none", (("none", "禁用拖放"), ("drag", "仅拖出"),
                         ("drop", "仅接收"), ("both", "拖出与接收"), ("internal", "内部移动")), "dragDropMode", "行为"),
                  flag("drop_indicator", "显示拖放位置提示", True, "showDropIndicator"),
                  integer("item_icon_width", "条目图标宽度", 0, high=256),
                  integer("item_icon_height", "条目图标高度", 0, high=256)]
        if cls != "SuperList":
            extra.append(choice("selection_behavior", "选择目标", "items" if cls not in TREES else "rows",
                                (("items", "单元格"), ("rows", "整行"), ("columns", "整列")), "selectionBehavior", "行为"))
    if cls in {"QListWidget", "QListView"}:
        extra += [choice("view_mode", "显示方式", "list", (("list", "列表"), ("icons", "图标网格")), group="外观"),
                  choice("list_flow", "排列方向", "default", (("default", "随显示方式"), ("left_to_right", "从左到右"), ("top_to_bottom", "从上到下"))),
                  choice("list_wrapping", "条目换行", "default", (("default", "随显示方式"), ("yes", "换行"), ("no", "不换行"))),
                  choice("list_resize_mode", "尺寸改变时排列", "fixed", (("fixed", "保持排列"), ("adjust", "重新排列")), "resizeMode"),
                  integer("spacing", "条目间距", 0, "spacing", high=200), flag("word_wrap", "文字自动换行", False, "wordWrap"),
                  flag("uniform_item_sizes", "条目尺寸一致", False, "uniformItemSizes"),
                  integer("grid_width", "网格单元宽度", 0, high=2000), integer("grid_height", "网格单元高度", 0, high=2000)]
    if cls == "QListWidget":
        extra.append(flag("sorting", "允许排序", False, group="行为"))
    if cls in TABLES:
        extra += [flag("show_horizontal_header", "显示水平表头", True, group="表头"),
                  flag("show_vertical_header", "显示垂直表头", True, group="表头"),
                  flag("show_grid", "显示网格", True, "showGrid", "外观"),
                  choice("grid_style", "网格线型", "solid", (("solid", "实线"), ("dash", "虚线"), ("dot", "点线"), ("dash_dot", "点划线")), "gridStyle"),
                  flag("word_wrap", "自动换行", True, "wordWrap"),
                  flag("corner_button", "显示全选角按钮", True, "cornerButtonEnabled", "表头"),
                  flag("sorting", "允许排序", False),
                  integer("row_height", "默认行高", 30, low=1, high=1000),
                  integer("column_width", "默认列宽", 100, low=1, high=2000),
                  flag("stretch_last_section", "末列填满", True, group="表头"),
                  choice("column_resize_mode", "列宽调整方式", "interactive", RESIZE, group="表头"),
                  choice("row_resize_mode", "行高调整方式", "interactive", RESIZE, group="表头")]
    if cls in TREES:
        extra += [flag("header_hidden", "隐藏表头", False, "headerHidden", "表头"),
                  flag("root_decorated", "显示根节点装饰", cls != "SuperList", "rootIsDecorated", "外观"),
                  flag("items_expandable", "允许展开节点", cls != "SuperList", "itemsExpandable"),
                  integer("indentation", "层级缩进", 20, "indentation", high=200),
                  flag("animated", "展开折叠动画", False, "animated"),
                  flag("expands_on_double_click", "双击展开节点", True, "expandsOnDoubleClick"),
                  flag("word_wrap", "文字自动换行", False, "wordWrap"),
                  flag("all_columns_show_focus", "整行显示焦点", False, "allColumnsShowFocus"),
                  flag("uniform_row_heights", "各行高度一致", cls == "SuperList", "uniformRowHeights"),
                  flag("sorting", "允许排序", False),
                  flag("expanded", "初始展开", True),
                  flag("stretch_last_section", "末列填满", True, group="表头"),
                  choice("column_resize_mode", "列宽调整方式", "interactive", RESIZE, group="表头")]
        if cls == "QTreeView":
            extra.append(text("header_text", "表头文本", "项目", group="表头"))
    if cls in TABLES | TREES:
        extra += [flag("header_movable", "允许拖动列顺序", cls in TREES, group="表头"),
                  flag("header_clickable", "允许点击列标题", True, group="表头"),
                  choice("header_alignment", "表头文字对齐", "left_vcenter" if cls in TREES else "center", ALIGNMENT, group="表头")]
    if cls == "QColumnView":
        extra += [flag("resize_grips_visible", "显示列宽调整手柄", True, "resizeGripsVisible", "外观"),
                  flag("preview_column_visible", "显示预览列", True, "previewColumnVisible", "外观")]
    if cls in {"QFormLayout", "QGridLayout"}:
        extra += [integer("horizontal_spacing", "水平间距", -1, low=-1, high=1000, group="布局"),
                  integer("vertical_spacing", "垂直间距", -1, low=-1, high=1000, group="布局")]
    if cls == "QFormLayout":
        extra += [choice("field_growth_policy", "字段扩展方式", "all_non_fixed", (("stay", "保持建议尺寸"),
                  ("expanding", "仅扩展型字段"), ("all_non_fixed", "扩展所有非固定字段")), group="布局"),
                  choice("row_wrap_policy", "表单换行方式", "dont_wrap", (("dont_wrap", "保持同行"),
                  ("long_rows", "过长时换行"), ("all_rows", "标签与字段分行")), group="布局"),
                  choice("label_alignment", "标签对齐", "left_vcenter", ALIGNMENT, group="布局"),
                  choice("form_alignment", "表单对齐", "top_left", ALIGNMENT, group="布局")]
    if cls == "QScrollArea":
        extra.append(choice("alignment", "内容对齐", "top_left", ALIGNMENT, "alignment"))
    if cls == "QSplitter":
        extra.append(flag("opaque_resize", "拖动时实时调整", True, "opaqueResize"))
    if cls == "QMdiArea":
        extra += [choice("tab_position", "表头朝向", "top", POSITIONS, group="表头"),
                  choice("tab_shape", "页签形状", "rounded", SHAPES, group="表头"),
                  flag("tabs_closable", "显示页签关闭按钮", True, group="表头"),
                  flag("tabs_movable", "允许移动页签", False, "tabsMovable", "表头"),
                  flag("document_mode", "文档模式", False, "documentMode", "表头"),
                  choice("activation_order", "窗口切换顺序", "creation", (("creation", "创建顺序"),
                         ("stacking", "叠放顺序"), ("history", "激活历史")), "activationOrder", "行为")]
    if cls == "QMdiSubWindow":
        extra += [integer("keyboard_single_step", "键盘移动步长", 5, "keyboardSingleStep", 1, 1000, "行为"),
                  integer("keyboard_page_step", "键盘大步长", 20, "keyboardPageStep", 1, 1000, "行为")]
    if cls in {"QDialog", "QWizard"}:
        extra.append(flag("size_grip", "显示尺寸手柄", False, "sizeGripEnabled"))
    if cls == "QDockWidget":
        extra += [flag("vertical_title_bar", "竖向标题栏", False, group="窗口"),
                  choice("allowed_areas", "允许停靠区域", "all", (("all", "全部边缘"), ("sides", "左右边缘"),
                         ("horizontal", "上下边缘"), ("none", "不允许重新停靠")), group="窗口")]
    if cls == "QWizard":
        extra += [flag("no_back_on_start", "首页隐藏上一步", True, group="页面"),
                  flag("no_back_on_last", "末页隐藏上一步", False, group="页面"),
                  flag("have_help_button", "显示帮助按钮", False, group="页面"),
                  flag("no_cancel_button", "隐藏取消按钮", False, group="页面"),
                  flag("independent_pages", "页面状态相互独立", False, group="页面")]
    if cls == "QWizardPage":
        extra += [flag("final_page", "作为结束页", False, group="页面"), flag("commit_page", "作为提交页", False, group="页面")]
    if cls == "QTabBar":
        extra += [choice("tab_position", "表头朝向", "top", POSITIONS, group="表头"),
                  choice("tab_shape", "页签形状", "rounded", SHAPES, group="表头"),
                  flag("draw_base", "绘制表头基线", True, "drawBase", "表头"),
                  flag("uses_scroll_buttons", "显示滚动按钮", True, "usesScrollButtons", "表头"),
                  flag("auto_hide", "单页自动隐藏", False, "autoHide", "表头"),
                  flag("document_mode", "文档模式", False, "documentMode", "表头"),
                  choice("elide_mode", "长标题省略方式", "right", ELIDE, "elideMode", "表头")]
    if cls == "QToolBar":
        extra += [flag("movable", "允许移动工具条", False), flag("floatable", "允许浮动工具条", False)]
    if cls == "QTimer":
        extra.append(choice("timer_type", "计时精度", "coarse", (("precise", "精确"), ("coarse", "粗略"),
                            ("very_coarse", "秒级粗略")), "timerType", "时钟"))
    if cls == "QAction":
        extra += [flag("auto_repeat", "长按重复触发", True, "autoRepeat"),
                  flag("icon_visible_in_menu", "菜单中显示图标", True, "iconVisibleInMenu", "外观"),
                  text("whats_this", "帮助说明", native="whatsThis", group="高级", multiline=True)]
    if cls == "CommonDialog":
        extra += [flag("use_native_dialog", "使用系统对话框", False, group="对话框"),
                  flag("read_only", "禁止在文件框中改动文件", False, group="对话框"),
                  flag("confirm_overwrite", "保存时确认覆盖", True, group="对话框"),
                  choice("file_view_mode", "文件显示方式", "detail", (("detail", "详细信息"), ("list", "列表")), group="对话框"),
                  text("initial_file", "初始文件名", group="对话框")]
    if cls == "PictureBox":
        extra += [choice("image_alignment", "图片对齐", "center", ALIGNMENT),
                  flag("smooth_scaling", "平滑缩放图片", True, group="外观"),
                  P("image_opacity", "图片不透明度", "外观", "float", 1.0, minimum=0, maximum=1)]
    if cls == "DrawingBoard":
        extra += [flag("border", "显示画板边框", True, group="外观"),
                  flag("antialiasing", "笔迹抗锯齿", True, group="绘图"),
                  choice("pen_style", "画笔线型", "solid", (("solid", "实线"), ("dash", "虚线"), ("dot", "点线"), ("dash_dot", "点划线")), group="绘图")]
    if cls in LAYOUTS:
        extra.append(choice("layout_alignment", "布局整体对齐", "fill", (("fill", "填满内容区"),) + ALIGNMENT, group="布局"))
    if cls == "QSplashScreen":
        extra.append(choice("message_alignment", "提示文字对齐", "bottom_center", ALIGNMENT))
    if cls == "QMenuBar":
        extra.append(flag("default_up", "菜单默认向上展开", False, "defaultUp"))
    if cls in {"QMessageBox", "QErrorMessage", "QInputDialog", "QColorDialog", "QFontDialog", "QProgressDialog"}:
        extra.append(flag("modal", "模态对话框", False, group="对话框"))
    if cls == "QMessageBox":
        extra += [text("informative_text", "补充说明", group="对话框", multiline=True),
                  text("detailed_text", "详细信息", group="对话框", multiline=True),
                  choice("text_format", "内容格式", "plain", (("plain", "纯文本"), ("rich", "富文本 HTML")), group="对话框"),
                  choice("default_button", "默认按钮", "auto", (("auto", "自动"), ("确定", "确定"), ("取消", "取消"),
                         ("是", "是"), ("否", "否"), ("应用", "应用"), ("关闭", "关闭"), ("重试", "重试")), group="对话框")]
    if cls == "QInputDialog":
        extra += [text("ok_text", "确定按钮文字", "确定", group="对话框"), text("cancel_text", "取消按钮文字", "取消", group="对话框"),
                  integer("integer_step", "整数步长", 1, low=1, high=1000000, group="数值"),
                  P("decimal_step", "小数步长", "数值", "float", 1.0, minimum=0.000001, maximum=1000000),
                  flag("multiline", "多行文本输入", False, group="对话框"),
                  P("input_items", "文本候选列表", "对话框", "string_list", ()),
                  flag("items_editable", "候选列表允许输入", False, group="对话框")]
    if cls in {"QColorDialog", "QFontDialog"}:
        extra.append(flag("use_native_dialog", "使用系统对话框", True, group="对话框"))
    if cls == "QFontDialog":
        extra.append(choice("font_filter", "可选字体范围", "all", (("all", "全部字体"), ("scalable", "可缩放字体"),
                            ("non_scalable", "点阵字体"), ("monospace", "等宽字体"), ("proportional", "非等宽字体")), group="对话框"))
    if cls == "QProgressDialog":
        extra.append(flag("auto_reset", "完成后自动重置", True, group="对话框"))
    if cls == "QGraphicsView":
        extra += [choice("alignment", "场景对齐", "center", ALIGNMENT, "alignment"),
                  choice("graphics_drag_mode", "鼠标拖动方式", "none", (("none", "不拖动"), ("hand", "手形平移"), ("rubber", "框选")), "dragMode", "行为"),
                  flag("antialiasing", "抗锯齿绘制", False, group="绘图"),
                  P("scene_background", "场景背景色", "绘图", "color", ""),
                  P("scene_text_color", "场景文字颜色", "绘图", "color", "#000000")]
    if cls == "QSvgWidget":
        extra += [flag("keep_aspect_ratio", "保持图形宽高比", False, group="外观"),
                  flag("animation_enabled", "允许 SVG 动画", True, group="行为")]
    if cls == "QRhiWidget":
        extra.append(flag("mirror_vertically", "垂直镜像", False, group="绘图"))
    if cls == "QOpenGLWidget":
        extra.append(choice("update_behavior", "画面更新方式", "full", (("full", "完整刷新"), ("partial", "保留未重绘区域")), group="绘图"))
    if cls == "QWebEngineView":
        extra += [flag("auto_load_images", "自动加载图片", True, group="内容"),
                  flag("local_storage", "允许本地存储", True, group="行为"),
                  flag("pdf_viewer", "内置 PDF 阅读器", True, group="行为"),
                  P("page_background", "网页背景色", "外观", "color", "#ffffff"),
                  integer("default_font_size", "网页默认字号", 16, low=1, high=96),
                  integer("minimum_font_size", "网页最小字号", 0, high=96)]
    existing = {prop.key for prop in spec.properties}
    native = {prop.qt_name for prop in spec.properties if prop.qt_name}
    # Preserve existing representations such as SuperList.header_visible and full_row.
    aliases = {"SuperList": {"header_hidden", "expanded"}}
    additions = []
    for prop in extra:
        if prop.key in existing or prop.key in aliases.get(cls, ()) or prop.qt_name and prop.qt_name in native:
            continue
        additions.append(prop)
        existing.add(prop.key)
        if prop.qt_name:
            native.add(prop.qt_name)
    properties = tuple(replace(prop, options=ALIGNMENT) if cls == "QLabel" and prop.key == "alignment" else
                       replace(prop, description="运行时可录入一至四组组合键；最大组数由快捷键序列长度控制，仅录入而不执行。")
                       if cls == "QKeySequenceEdit" and prop.key == "key_sequence" else prop
                       for prop in spec.properties)
    return replace(spec, properties=properties + tuple(additions))
