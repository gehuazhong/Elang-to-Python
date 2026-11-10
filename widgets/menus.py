"""窗口菜单栏与菜单项；通过菜单编辑器创建层级。"""

from core.metadata import EventSpec as E, PropertySpec as P, WidgetSpec


def register_menu_widgets(registry, common):
    registry.register(WidgetSpec(
        "builtin.menu_bar", "菜单栏", "窗口结构", "QMenuBar", 1, "menu_bar", (800, 28), "menu_bar",
        (P("bar_height", "菜单栏高度", "外观", "int", 28, minimum=24, maximum=64),) + common,
        toolbox=False,
    ))
    registry.register(WidgetSpec(
        "builtin.menu_item", "菜单项", "窗口结构", "QAction", 1, "menu", (1, 1), "menu",
        (P("text", "标题", "基本", "string", "新菜单", "text",
           description="标题中 & 后的字符为访问键，例如 文件(&F)；分隔线在菜单编辑器中设置。"),
         P("shortcut", "快捷键", "行为", "shortcut", "",
           description="例如 Ctrl+O 或 Ctrl+Shift+S；快捷键用于没有子菜单的普通菜单项。"),
         P("separator", "分隔线", "基本", "bool", False),
         P("checkable", "可选中", "行为", "bool", False, "checkable"),
         P("checked", "选中", "行为", "bool", False, "checked"),
         P("enabled", "启用", "行为", "bool", True, "enabled"),
         P("visible", "可视", "行为", "bool", True, "visible"),
         P("status_tip", "状态提示", "行为", "string", "", "statusTip")),
        toolbox=False, events=(E("clicked", "被单击", "triggered"),),
    ))
