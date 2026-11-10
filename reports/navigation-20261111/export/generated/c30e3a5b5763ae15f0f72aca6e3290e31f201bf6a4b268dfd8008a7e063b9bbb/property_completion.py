"""补充属性的转换及复合适配，独立导出携带同一份实现。"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QCursor, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QComboBox, QDockWidget,
    QFormLayout, QGraphicsView, QHeaderView, QLCDNumber, QListView, QListWidget, QMdiArea,
    QProgressBar, QSizePolicy, QTabBar, QTableView, QTableWidget, QTabWidget, QTreeView,
    QWizard, QWizardPage, QWidget)


ALIGNMENTS = {
    "left_vcenter": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
    "center": Qt.AlignmentFlag.AlignCenter,
    "right_vcenter": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    **{y + "_" + x: vertical | horizontal for y, vertical in
       (("top", Qt.AlignmentFlag.AlignTop), ("bottom", Qt.AlignmentFlag.AlignBottom))
       for x, horizontal in (("left", Qt.AlignmentFlag.AlignLeft), ("center", Qt.AlignmentFlag.AlignHCenter), ("right", Qt.AlignmentFlag.AlignRight))},
}
ELIDE = {"none": Qt.TextElideMode.ElideNone, "left": Qt.TextElideMode.ElideLeft,
         "middle": Qt.TextElideMode.ElideMiddle, "right": Qt.TextElideMode.ElideRight}
SCROLL = {"as_needed": Qt.ScrollBarPolicy.ScrollBarAsNeeded, "always": Qt.ScrollBarPolicy.ScrollBarAlwaysOn,
          "never": Qt.ScrollBarPolicy.ScrollBarAlwaysOff}
NATIVE_ENUMS = {
    "alignment": ALIGNMENTS, "horizontal_policy": SCROLL, "vertical_policy": SCROLL,
    "text_elide_mode": ELIDE, "elide_mode": ELIDE,
    "cursor_move_style": {"logical": Qt.CursorMoveStyle.LogicalMoveStyle, "visual": Qt.CursorMoveStyle.VisualMoveStyle},
    "size_adjust_policy": {"always": QComboBox.SizeAdjustPolicy.AdjustToContents,
                           "first_show": QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow,
                           "minimum": QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon},
    "correction_mode": {"previous": QAbstractSpinBox.CorrectionMode.CorrectToPreviousValue,
                        "nearest": QAbstractSpinBox.CorrectionMode.CorrectToNearestValue},
    "step_type": {"default": QAbstractSpinBox.StepType.DefaultStepType, "adaptive": QAbstractSpinBox.StepType.AdaptiveDecimalStepType},
    "text_direction": {"top_to_bottom": QProgressBar.Direction.TopToBottom, "bottom_to_top": QProgressBar.Direction.BottomToTop},
    "vertical_scroll_mode": {"item": QAbstractItemView.ScrollMode.ScrollPerItem, "pixel": QAbstractItemView.ScrollMode.ScrollPerPixel},
    "horizontal_scroll_mode": {"item": QAbstractItemView.ScrollMode.ScrollPerItem, "pixel": QAbstractItemView.ScrollMode.ScrollPerPixel},
    "list_resize_mode": {"fixed": QListView.ResizeMode.Fixed, "adjust": QListView.ResizeMode.Adjust},
    "grid_style": {"solid": Qt.PenStyle.SolidLine, "dash": Qt.PenStyle.DashLine, "dot": Qt.PenStyle.DotLine, "dash_dot": Qt.PenStyle.DashDotLine},
    "number_mode": {"decimal": QLCDNumber.Mode.Dec, "hex": QLCDNumber.Mode.Hex, "octal": QLCDNumber.Mode.Oct, "binary": QLCDNumber.Mode.Bin},
    "activation_order": {"creation": QMdiArea.WindowOrder.CreationOrder, "stacking": QMdiArea.WindowOrder.StackingOrder,
                         "history": QMdiArea.WindowOrder.ActivationHistoryOrder},
    "graphics_drag_mode": {"none": QGraphicsView.DragMode.NoDrag, "hand": QGraphicsView.DragMode.ScrollHandDrag,
                           "rubber": QGraphicsView.DragMode.RubberBandDrag},
    "timer_type": {"precise": Qt.TimerType.PreciseTimer, "coarse": Qt.TimerType.CoarseTimer, "very_coarse": Qt.TimerType.VeryCoarseTimer},
    "drag_drop_mode": {"none": QAbstractItemView.DragDropMode.NoDragDrop, "drag": QAbstractItemView.DragDropMode.DragOnly,
                       "drop": QAbstractItemView.DragDropMode.DropOnly, "both": QAbstractItemView.DragDropMode.DragDrop,
                       "internal": QAbstractItemView.DragDropMode.InternalMove},
}
SHARED_KEYS = {"cursor_shape", "focus_policy", "style_sheet", "size_policy_horizontal", "size_policy_vertical", "layout_alignment"}
COMPOSITE_KEYS = {
    "CommonDialog": {"use_native_dialog", "read_only", "confirm_overwrite", "file_view_mode", "initial_file"},
    "PictureBox": {"image_alignment", "smooth_scaling", "image_opacity"},
    "DrawingBoard": {"border", "antialiasing", "pen_style"}, "QSplashScreen": {"message_alignment"},
    "QLineEdit": {"input_mask"}, "QKeySequenceEdit": {"maximum_sequence_length"},
    **{cls: {"item_icon_width", "item_icon_height", "header_movable", "header_clickable", "header_alignment",
             "column_resize_mode", "row_resize_mode", "column_width", "row_height", "sorting", "expanded", "header_text",
             "show_horizontal_header", "show_vertical_header", "stretch_last_section", "grid_width", "grid_height", "list_flow", "list_wrapping", "view_mode"}
       for cls in ("QListWidget", "QTableWidget", "QTreeWidget", "SuperList", "QListView", "QTableView", "QTreeView", "QColumnView", "QUndoView")},
    **{cls: {"horizontal_spacing", "vertical_spacing", "field_growth_policy", "row_wrap_policy", "label_alignment", "form_alignment"}
       for cls in ("QFormLayout", "QGridLayout")},
    "QMdiArea": {"tab_position", "tab_shape", "tabs_closable"},
    "QTabBar": {"tab_position", "tab_shape"}, "QDockWidget": {"allowed_areas", "vertical_title_bar"},
    "QWizard": {"no_back_on_start", "no_back_on_last", "have_help_button", "no_cancel_button", "independent_pages"},
    "QWizardPage": {"final_page", "commit_page"}, "QToolBar": {"movable", "floatable"},
    **{cls: {"modal", "informative_text", "detailed_text", "text_format", "default_button", "ok_text", "cancel_text",
             "integer_step", "decimal_step", "multiline", "input_items", "items_editable", "use_native_dialog", "font_filter", "auto_reset"}
       for cls in ("QMessageBox", "QErrorMessage", "QInputDialog", "QColorDialog", "QFontDialog", "QProgressDialog")},
    "QGraphicsView": {"antialiasing", "scene_background", "scene_text_color"},
    "QSvgWidget": {"keep_aspect_ratio", "animation_enabled"}, "QRhiWidget": {"mirror_vertically"},
    "QOpenGLWidget": {"update_behavior"},
    "QWebEngineView": {"auto_load_images", "local_storage", "pdf_viewer", "page_background", "default_font_size", "minimum_font_size"},
}


def header_options(header, values):
    if "header_movable" in values:
        header.setSectionsMovable(values["header_movable"])
        header.setSectionsClickable(values["header_clickable"])
        header.setDefaultAlignment(ALIGNMENTS[values["header_alignment"]])
    mode = values.get("column_resize_mode", "interactive")
    header.setSectionResizeMode({"interactive": QHeaderView.ResizeMode.Interactive, "fixed": QHeaderView.ResizeMode.Fixed,
                                "stretch": QHeaderView.ResizeMode.Stretch, "contents": QHeaderView.ResizeMode.ResizeToContents}[mode])
    if mode != "interactive":
        header.setStretchLastSection(False)


def apply_tree_expansion(widget, expanded):
    model = widget.model()
    content = getattr(widget, "_tree_source", None)
    if (getattr(widget, "_expanded_model", None) is not model or
            getattr(widget, "_expanded_content", None) != content or
            getattr(widget, "_expanded_source", None) != expanded):
        widget.expandAll() if expanded else widget.collapseAll()
        widget._expanded_model = model
        widget._expanded_content = content
        widget._expanded_source = expanded


def apply_completed_properties(widget, values):
    if isinstance(widget, QWidget) and "cursor_shape" in values:
        if not hasattr(widget, "_completion_defaults"):
            widget._completion_defaults = (QCursor(widget.cursor()), widget.focusPolicy(), widget.styleSheet(), widget.sizePolicy())
        cursor, focus, style, policy = widget._completion_defaults
        cursors = {"arrow": Qt.CursorShape.ArrowCursor, "pointing_hand": Qt.CursorShape.PointingHandCursor,
                   "ibeam": Qt.CursorShape.IBeamCursor, "cross": Qt.CursorShape.CrossCursor, "wait": Qt.CursorShape.WaitCursor,
                   "forbidden": Qt.CursorShape.ForbiddenCursor, "open_hand": Qt.CursorShape.OpenHandCursor, "closed_hand": Qt.CursorShape.ClosedHandCursor}
        widget.setCursor(cursor if values["cursor_shape"] == "default" else QCursor(cursors[values["cursor_shape"]]))
        policies = {"none": Qt.FocusPolicy.NoFocus, "tab": Qt.FocusPolicy.TabFocus, "click": Qt.FocusPolicy.ClickFocus,
                    "strong": Qt.FocusPolicy.StrongFocus, "wheel": Qt.FocusPolicy.WheelFocus}
        widget.setFocusPolicy(focus if values["focus_policy"] == "default" else policies[values["focus_policy"]])
        widget.setStyleSheet(values["style_sheet"] or style)
        if "size_policy_horizontal" in values:
            result = QSizePolicy(policy)
            names = {"fixed": "Fixed", "minimum": "Minimum", "maximum": "Maximum", "preferred": "Preferred",
                     "expanding": "Expanding", "minimum_expanding": "MinimumExpanding", "ignored": "Ignored"}
            for direction, setter in (("horizontal", result.setHorizontalPolicy), ("vertical", result.setVerticalPolicy)):
                selected = values["size_policy_" + direction]
                if selected != "default":
                    setter(getattr(QSizePolicy.Policy, names[selected]))
            widget.setSizePolicy(result)
    if isinstance(widget, QAbstractItemView) and "item_icon_width" in values:
        if not hasattr(widget, "_completion_icon_size"):
            widget._completion_icon_size = widget.iconSize()
        size = widget._completion_icon_size
        widget.setIconSize(QSize(values["item_icon_width"] or size.width(), values["item_icon_height"] or size.height()))
    if isinstance(widget, QListView) and "list_flow" in values:
        icons = values["view_mode"] == "icons"
        widget.setViewMode(QListView.ViewMode.IconMode if icons else QListView.ViewMode.ListMode)
        widget.setFlow(QListView.Flow.LeftToRight if values["list_flow"] == "left_to_right" or
                       values["list_flow"] == "default" and icons else QListView.Flow.TopToBottom)
        widget.setWrapping(icons if values["list_wrapping"] == "default" else values["list_wrapping"] == "yes")
        widget.setGridSize(QSize(values["grid_width"] or max(1, widget.sizeHintForColumn(0)),
                                values["grid_height"] or max(1, widget.sizeHintForRow(0)))
                           if values["grid_width"] or values["grid_height"] else QSize())
    if isinstance(widget, (QTableView, QTreeView, QListWidget)) and "sorting" in values:
        widget.setSortingEnabled(values["sorting"])
    if isinstance(widget, QTableView) and "column_resize_mode" in values:
        from .widget_properties import apply_column_widths
        widget.horizontalHeader().setVisible(values["show_horizontal_header"])
        widget.verticalHeader().setVisible(values["show_vertical_header"])
        apply_column_widths(widget.horizontalHeader(), values["table_data"], values["column_width"], values["stretch_last_section"])
        header_options(widget.horizontalHeader(), values)
        widget.verticalHeader().setMinimumSectionSize(1)
        widget.verticalHeader().setDefaultSectionSize(values["row_height"])
        widget.verticalHeader().setSectionResizeMode({"interactive": QHeaderView.ResizeMode.Interactive,
            "fixed": QHeaderView.ResizeMode.Fixed, "stretch": QHeaderView.ResizeMode.Stretch,
            "contents": QHeaderView.ResizeMode.ResizeToContents}[values["row_resize_mode"]])
    if isinstance(widget, QTreeView) and "column_resize_mode" in values:
        if "header_text" in values and widget.model() is not None:
            widget.model().setHeaderData(0, Qt.Orientation.Horizontal, values["header_text"])
        widths = values.get("table_data", {}).get("column_widths", ())
        widget.header().setStretchLastSection(values["stretch_last_section"] and (not widths or not widths[-1]))
        header_options(widget.header(), values)
        if "expanded" in values:
            apply_tree_expansion(widget, values["expanded"])
    layout = getattr(widget, "native_layout", None)
    if layout is not None and "layout_alignment" in values:
        layout.setAlignment(Qt.AlignmentFlag(0) if values["layout_alignment"] == "fill" else ALIGNMENTS[values["layout_alignment"]])
    if layout is not None and "horizontal_spacing" in values:
        layout.setHorizontalSpacing(values["spacing"] if values["horizontal_spacing"] < 0 else values["horizontal_spacing"])
        layout.setVerticalSpacing(values["spacing"] if values["vertical_spacing"] < 0 else values["vertical_spacing"])
        if isinstance(layout, QFormLayout):
            layout.setFieldGrowthPolicy({"stay": QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint,
                "expanding": QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow, "all_non_fixed": QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow}[values["field_growth_policy"]])
            layout.setRowWrapPolicy({"dont_wrap": QFormLayout.RowWrapPolicy.DontWrapRows,
                "long_rows": QFormLayout.RowWrapPolicy.WrapLongRows, "all_rows": QFormLayout.RowWrapPolicy.WrapAllRows}[values["row_wrap_policy"]])
            layout.setLabelAlignment(ALIGNMENTS[values["label_alignment"]])
            layout.setFormAlignment(ALIGNMENTS[values["form_alignment"]])
    if isinstance(widget, QTabBar) and "tab_position" in values:
        shape = "Rounded" if values["tab_shape"] == "rounded" else "Triangular"
        direction = {"top": "North", "bottom": "South", "left": "West", "right": "East"}[values["tab_position"]]
        widget.setShape(getattr(QTabBar.Shape, shape + direction))
    if isinstance(widget, QMdiArea) and "tab_position" in values:
        widget.setTabPosition({"top": QTabWidget.TabPosition.North, "bottom": QTabWidget.TabPosition.South,
                               "left": QTabWidget.TabPosition.West, "right": QTabWidget.TabPosition.East}[values["tab_position"]])
        widget.setTabShape(QTabWidget.TabShape.Rounded if values["tab_shape"] == "rounded" else QTabWidget.TabShape.Triangular)
        widget.setTabsClosable(values["tabs_closable"])
    if isinstance(widget, QDockWidget) and "allowed_areas" in values:
        widget.setAllowedAreas({"all": Qt.DockWidgetArea.AllDockWidgetAreas,
            "sides": Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
            "horizontal": Qt.DockWidgetArea.TopDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea,
            "none": Qt.DockWidgetArea.NoDockWidgetArea}[values["allowed_areas"]])
        features = widget.features()
        flag = QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar
        widget.setFeatures(features | flag if values["vertical_title_bar"] else features & ~flag)
    if isinstance(widget, QWizard) and "no_back_on_start" in values:
        for key, flag in (("no_back_on_start", "NoBackButtonOnStartPage"), ("no_back_on_last", "NoBackButtonOnLastPage"),
                          ("have_help_button", "HaveHelpButton"), ("no_cancel_button", "NoCancelButton"), ("independent_pages", "IndependentPages")):
            widget.setOption(getattr(QWizard.WizardOption, flag), values[key])
    if isinstance(widget, QWizardPage) and "final_page" in values:
        widget.setFinalPage(values["final_page"])
        widget.setCommitPage(values["commit_page"])
    if isinstance(widget, QGraphicsView) and "antialiasing" in values:
        widget.setRenderHint(QPainter.RenderHint.Antialiasing, values["antialiasing"])
        widget.setBackgroundBrush(QColor(values["scene_background"]) if values["scene_background"] else Qt.BrushStyle.NoBrush)
        for item in widget.scene().items():
            if hasattr(item, "setDefaultTextColor"):
                item.setDefaultTextColor(QColor(values["scene_text_color"]))


def finish_completed_properties(controls):
    # The builder's general visible property must not override QTabBar.autoHide.
    for widget in controls.values():
        if isinstance(widget, QTabBar) and widget.autoHide() and widget.count() < 2:
            widget.hide()
