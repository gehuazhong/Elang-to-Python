"""设计器外壳与编辑标记的颜色；不参与被设计窗口的运行时配色。"""

COLORS = {
    "activity": "#181818", "background": "#1f1f1f", "border": "#313131",
    "editor": "#1f1f1f", "focus": "#0078d4", "hover": "#2a2d2e",
    "input": "#313131", "muted": "#9d9d9d", "selected": "#04395e",
    "sidebar": "#181818", "status": "#007acc", "text": "#cccccc",
    "title": "#181818", "white": "#ffffff", "disabled": "#777777",
    "button": "#0e639c", "button_hover": "#1177bb", "secondary": "#3a3d41",
    "line_hover": "#6b6b6b", "error": "#f48771", "link": "#4daafc",
}

ACCENT = COLORS["focus"]
ACCENT_SOFT = COLORS["selected"]
TEXT = COLORS["text"]
MUTED = COLORS["muted"]
LINE = COLORS["border"]
PANEL = COLORS["sidebar"]
SURFACE = COLORS["editor"]
CANVAS = COLORS["background"]
