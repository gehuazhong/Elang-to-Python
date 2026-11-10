"""确定性生成已支持组件的界面代码，拒绝静默遗漏项目能力。"""

from __future__ import annotations

import ast
import builtins
import keyword
from pathlib import Path

from core.build_plan import compile_plan
from core.errors import require
from core.events import event_bindings
from core.models import ProjectModel, thaw
from core.registry import WidgetRegistry
from core.window_scaling import scale_base_size, scale_items
from widgets.catalog import QT_WIDGET_CLASSES, COMPONENT_CLASSES, ADAPTER_CLASSES, ADVANCED_CLASSES, SUPPORTED_SLOTS
from core.image_values import image_bytes, image_filename


def generate_files(model: ProjectModel, registry: WidgetRegistry) -> dict[str, bytes]:
    plan = compile_plan(model, registry, "代码导出")
    require(all(node.slot in SUPPORTED_SLOTS for node in plan.nodes), "项目包含尚未支持导出的组件。")
    selected_events = event_bindings(model, registry)
    if any("slot" in binding for binding in selected_events):
        from runtime.builder import verify_event_targets
        verify_event_targets(model, registry, selected_events)
    require(not model.data["resources"], "项目包含未接入的旧式外部资源引用；图片框和画板请通过图片属性导入，不能遗漏资源导出。")
    require(not model.data["extensions"], "项目包含尚未支持导出的扩展。")
    require(set(model.data) <= {"format", "schema_version", "document_id", "name", "root_id", "connections",
                               "handlers", "resources", "tab_order", "canvas", "codegen", "extensions"},
            "项目包含未知顶层数据，无法保证完整导出。")
    require(plan.nodes[0].properties.get("visible", True), "窗口的可见属性已关闭，请开启后导出。")
    settings = model.data["codegen"]
    require(set(settings) <= {"template_id", "window_class", "entry_file"}, "代码生成配置包含未知选项。")
    require(settings.get("template_id", "builtin.pyside6") == "builtin.pyside6", "代码模板尚不受支持。")
    require(settings.get("entry_file", "main.py") == "main.py", "当前导出使用固定入口 main.py。")
    class_name = settings.get("window_class", "MainWindow")
    require(isinstance(class_name, str) and class_name.isascii() and class_name.isidentifier()
            and not keyword.iskeyword(class_name) and not class_name.startswith("_")
            and class_name not in vars(builtins) and class_name not in {"create_window", "configure_application"},
            "窗口类名称必须是有效且不冲突的英文标识符。")
    known = COMPONENT_CLASSES
    assets: dict[str, bytes] = {}
    lines = ['"""自动生成的界面模块；事件业务请写入 event_handlers，初始化请写入 handlers.py。"""',
             "from __future__ import annotations", "", "from PySide6.QtCore import Qt as _Qt, QObject as _QObject, QTimer as _QTimer",
             "from PySide6.QtGui import QAction as _QAction",
             "from PySide6.QtWidgets import " + ", ".join(f"{name} as _{name}" for name in sorted(QT_WIDGET_CLASSES)),
             "from .easy_widgets import " + ", ".join(f"{name} as _{name}" for name in sorted(ADAPTER_CLASSES)),
             "from .easy_widgets import apply_easy_properties as _apply_easy_properties, start_components as _start_components, image_asset as _image_asset",
             "from .appearance import apply_appearance as _apply_appearance, apply_window_options as _apply_window_options",
             "from .widget_properties import apply_widget_properties as _apply_widget_properties, apply_content_margins as _apply_content_margins",
             "from .widget_properties import ContainerGroupBox as _QGroupBox, ContainerFrame as _QFrame",
             "from .menus import apply_menu_properties as _apply_menu_properties, arrange_menus as _arrange_menus",
             "from .control_features import apply_control_features as _apply_control_features, finish_group_states as _finish_group_states",
             "from .navigation import apply_navigation_style as _apply_navigation_style, configure_navigation as _configure_navigation",
             "from .property_completion import apply_completed_properties as _apply_completed_properties, finish_completed_properties as _finish_completed_properties",
             "from .advanced_widgets import ADVANCED_FACTORIES as _advanced, content_host as _content_host, apply_advanced_properties as _apply_advanced, arrange_advanced as _arrange_advanced, start_advanced as _start_advanced",
             "from .layout.scaling import ScaleItem as _ScaleItem",
             "from .layout.runtime import WindowScaler as _WindowScaler",
             "from .application import configure_application", "", f"class {class_name}(_QMainWindow):",
             "    def __init__(self) -> None:", "        super().__init__()", "        self.setup_ui()", "",
             "    def setup_ui(self) -> None:", "        self.controls: dict[str, _QObject] = {}",
             "        advanced_records = []"]
    expressions: dict[str, str] = {}
    for node in plan.nodes:
        original = model.nodes[node.id]
        spec = registry.require(node.type_id)
        require(original.layout is None or (set(original.layout) <= {"kind", "margins", "spacing"}
                and not any(original.layout["margins"])), "当前导出尚不支持非零布局边距或扩展布局数据。")
        require(spec.qt_class in known and not original.extensions and not original.extra
                and set(original.properties) <= {prop.key for prop in spec.properties},
                f"“{node.name}”包含尚未支持导出的属性或扩展。")
        ref = f"self.controls[{original.code_name!r}]"
        expressions[node.id] = ref
        parent = f"_content_host({expressions.get(node.parent_id, 'self')})"
        constructor = f"_advanced[{spec.qt_class!r}]" if spec.qt_class in ADVANCED_CLASSES else f"_{spec.qt_class}"
        lines += [f"        # 创建{spec.label}并应用已校验的属性。",
                  f"        {ref} = " + ("self" if node.slot == "root" else f"{constructor}({parent})"),
                  f"        {ref}.setObjectName({node.name!r})"]
        if node.slot == "central":
            lines.append(f"        self.setCentralWidget({ref})")
        elif node.slot == "tool_bar":
            lines.append(f"        self.addToolBar(_Qt.ToolBarArea.TopToolBarArea, {ref})")
        elif node.slot == "status_bar":
            lines.append(f"        self.setStatusBar({ref})")
        if spec.qt_class == "QLabel":
            lines.append(f"        {ref}.setTextFormat(_Qt.TextFormat.PlainText)")
        bindings = tuple((prop.key, prop.qt_name, prop.label) for prop in spec.properties)
        values = thaw(node.properties)
        pictures = {prop.key: values[prop.key] for prop in spec.properties
                    if prop.value_type == "image" and values.get(prop.key)}
        for key, picture in pictures.items():
            assets[image_filename(picture)] = image_bytes(picture)
            values[key] = ""
        lines.append(f"        values = {values!r}")
        for key, picture in pictures.items():
            lines.append(f"        values[{key!r}] = _image_asset(__file__, {image_filename(picture)!r})")
        parent_code = model.nodes[node.parent_id].code_name if node.parent_id else None
        lines.append(f"        advanced_records.append(({original.code_name!r}, {parent_code!r}, {node.slot!r}, values))")
        lines.append(f"        _apply_widget_properties({ref}, values, {bindings!r})")
        lines.append(f"        _apply_easy_properties({ref}, values)")
        lines.append(f"        _apply_advanced({ref}, values)")
        lines.append(f"        _apply_control_features({ref}, values)")
        lines.append(f"        _apply_menu_properties({ref}, values)")
        lines.append(f"        _apply_completed_properties({ref}, values)")
        if node.slot not in {"non_visual", "menu"}:
            lines.append(f"        _apply_appearance({ref}, values)")
            lines.append(f"        _apply_navigation_style({ref}, values)")
        if node.slot == "root":
            lines.append("        _apply_window_options(self, values)")
        rect = node.geometry
        if rect:
            if node.slot == "root":
                lines += [f"        self.resize({rect.width}, {rect.height})", f"        self.move({rect.x}, {rect.y})"]
                if node.properties.get("border_style") == "fixed":
                    lines.append(f"        self.setFixedSize({rect.width}, {rect.height})")
            else:
                lines += [f"        offset = {parent}.contentsRect().topLeft()",
                          f"        {ref}.setGeometry({rect.x} + offset.x(), {rect.y} + offset.y(), {rect.width}, {rect.height})"]
        if node.slot not in {"non_visual", "menu"}:
            lines.append(f"        _apply_content_margins({ref}, values)")
        if node.slot == "pages":
            lines.append(f"        {ref}.setProperty('page_visible', {node.properties.get('visible', True)!r})")
        if node.slot not in {"root", "non_visual"}:
            lines.append(f"        {ref}.setVisible({node.properties.get('visible', True)!r})")
    for node in plan.nodes:
        if node.type_id == "builtin.tab_widget":
            children = [f"({expressions[page.id]}, {page.properties['text']!r})" for page in plan.nodes if page.parent_id == node.id and page.slot == "pages"]
            lines.append(f"        {expressions[node.id]}.set_pages([{', '.join(children)}], {node.properties['current_index']})")
    menu_records = [(model.nodes[node.id].code_name, model.nodes[node.parent_id].code_name, node.slot)
                    for node in plan.nodes if node.slot in {"menu_bar", "menu"}]
    lines.append(f"        _arrange_menus(self, self.controls, {menu_records!r})")
    group_records = [(model.nodes[node.id].code_name, node.properties.get("checked", False)) for node in plan.nodes
                     if node.type_id == "builtin.group_box"]
    lines.append(f"        _finish_group_states(self.controls, {group_records!r})")
    lines.append("        _arrange_advanced(self, self.controls, advanced_records)")
    lines.append("        _finish_completed_properties(self.controls)")
    lines.append("        _configure_navigation(self.controls, advanced_records)")
    lines += ["        self.ensurePolished()", "        self.layout().activate()"]
    for node in sorted((node for node in plan.nodes if node.stack_order is not None), key=lambda item: (item.parent_id or "", item.stack_order)):
        lines.append(f"        {expressions[node.id]}.raise_()")
    for first, second in zip(plan.tab_order, plan.tab_order[1:]):
        lines.append(f"        _QWidget.setTabOrder({expressions[first]}, {expressions[second]})")
    if plan.nodes[0].properties.get("scale_children", False):
        items = scale_items(plan.nodes)
        lines += ["        # 保留设计基准，每次窗口拉伸均重新计算，字号保持用户设置。",
                  "        scale_items = ("]
        for item in items:
            lines.append(f"            _ScaleItem({item.key!r}, {item.parent!r}, {item.kind!r}, {item.rect!r}, {item.margins!r}, {item.minimum!r}, {item.page_insets!r}),")
        lines += ["        )", "        scale_controls = {"]
        for item in items:
            lines.append(f"            {item.key!r}: {expressions[item.key]},")
        lines += ["        }", f"        self._component_scaler = _WindowScaler(self, self.centralWidget(), {scale_base_size(plan.nodes)!r}, scale_items, scale_controls)"]
    lines += ["        from .events import connect_exported_events",
              f"        self._event_connections = connect_exported_events(self, {selected_events!r}, __file__)",
              "        _start_components(self.controls)", "        _start_advanced(self.controls)"]
    lines += ["", f"def create_window() -> {class_name}:", f"    return {class_name}()", ""]
    source = "\n".join(lines)
    ast.parse(source)
    base = Path(__file__).resolve().parents[1]
    return {"ui_main.py": source.encode("utf-8"), "appearance.py": (base / "runtime/appearance.py").read_bytes(),
            "widget_properties.py": (base / "runtime/widget_properties.py").read_bytes(),
            "easy_widgets.py": (base / "runtime/easy_widgets.py").read_bytes(), **assets,
            "events.py": (base / "runtime/events.py").read_bytes(),
            "menus.py": (base / "runtime/menus.py").read_bytes(),
            "control_features.py": (base / "runtime/control_features.py").read_bytes(),
            "navigation.py": (base / "runtime/navigation.py").read_bytes(),
            "property_completion.py": (base / "runtime/property_completion.py").read_bytes(),
            **{name: (base / "runtime" / name).read_bytes() for name in
               ("advanced_widgets.py", "advanced_containers.py", "advanced_dialogs.py", "advanced_views.py", "advanced_graphics.py")},
            **{f"layout/{name}": (base / "layout" / name).read_bytes() for name in ("__init__.py", "scaling.py", "runtime.py", "containers.py")},
            "application.py": (base / "runtime/application.py").read_bytes()}
