"""按提供的兔子工具截图制作可编辑的个人中心示例。"""

from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QPainterPath
from PySide6.QtSvg import QSvgRenderer


BACKGROUND = "#111111"
SIDEBAR = "#262626"
TEXT = "#dddddd"
MUTED = "#858585"
ROOT = Path(__file__).resolve().parents[1]
BUNNY = ('<path d="M35 60 C24 45 19 23 29 16 C43 7 54 28 59 48 '
         'L65 47 C68 27 69 9 82 8 C100 5 100 29 94 47 '
         'C116 55 130 70 127 93 C124 118 104 134 72 136 '
         'C43 139 22 127 18 105 C14 84 23 69 35 60Z"/>')


def svg(body, width=24, height=24):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{body}</svg>')


def image_value(image):
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("无法编码示例图片")
    return bytes(data.toBase64()).decode("ascii")


def rendered_image(source, width, height):
    image = QImage(width * 2, height * 2, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    QSvgRenderer(source.encode("utf-8")).render(painter)
    painter.end()
    return image_value(image)


def avatar_image():
    cached = ROOT / "uidemo/assets/rabbit-avatar.png"
    if cached.exists():
        return image_value(QImage(str(cached)))
    reference = QImage(str(ROOT / "reports/QQ20261109-153349.jpg"))
    if reference.isNull():
        raise FileNotFoundError("需要参考图或 uidemo/assets/rabbit-avatar.png 来生成头像")
    # Keep only the supplied avatar; the surrounding screenshot is not embedded.
    avatar = QImage(144, 144, QImage.Format.Format_ARGB32_Premultiplied)
    avatar.fill(Qt.GlobalColor.transparent)
    painter = QPainter(avatar)
    painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    clip = QPainterPath()
    clip.addEllipse(QRectF(1, 1, 142, 142))
    painter.setClipPath(clip)
    painter.drawImage(QRectF(0, 0, 144, 144), reference, QRectF(214, 104, 72, 72))
    painter.end()
    cached.parent.mkdir(parents=True, exist_ok=True)
    if not avatar.save(str(cached)):
        raise RuntimeError("无法保存头像素材")
    return image_value(avatar)


def profile():
    from uidemo.build_examples import Design

    d = Design("兔子工具 · 个人中心", 1000, 654, BACKGROUND)
    d.set("main_window", border_style="none", foreground_color=TEXT, font_size=9)

    def label(code, text, x, y, width, height=24, **options):
        options.setdefault("color", TEXT)
        options.setdefault("size", 9)
        return d.label(code, text, x, y, width, height, **options)

    def vector(code, name, source, x, y, width, height, parent="central_widget"):
        return d.add("svg_widget", code, name, x, y, width, height, parent=parent, svg_data=source)

    def hit(code, name, x, y, width, height, parent="central_widget"):
        d.add("button", code, name, x, y, width, height, parent=parent,
              text="", flat=True, tool_tip=name, foreground_color=TEXT)
        d.event(code)

    d.frame("sidebar", "左侧导航", 0, 0, 182, 654, SIDEBAR)
    vector("brand_icon", "兔子标志", svg(f'<g fill="{TEXT}">{BUNNY}</g>', 144, 144),
           38, 50, 24, 28, "sidebar")
    label("brand", "兔子工具", 64, 48, 100, 34, size=16, bold=True, parent="sidebar")
    vector("nav_active", "当前导航背景", svg('<rect width="155" height="36" rx="5" fill="#383838"/>', 155, 36),
           14, 148, 155, 36, "sidebar")
    icons = {
        "home": '<path d="m3 10 9-7 9 7v10H3Z"/><rect x="9" y="12" width="6" height="6" rx="1"/>',
        "profile": '<circle cx="12" cy="10" r="7"/><path d="M5 21h14M12 17v4"/>',
        "tools_one": '<ellipse cx="12" cy="12" rx="9" ry="7"/><path d="m4 18 16-12M7 21l4-3"/>',
        "tools_two": '<circle cx="12" cy="12" r="9"/><path d="M8 9v2m8-2v2m-4 3v3"/>',
        "settings": '<path d="m12 2 8 5v10l-8 5-8-5V7Z"/><circle cx="12" cy="12" r="3"/>',
    }
    for key, text, y in (("home", "首页", 108), ("profile", "个人中心", 148),
                         ("tools_one", "壹号工具箱", 237), ("tools_two", "贰号工具箱", 278),
                         ("settings", "设置", 368)):
        vector("icon_" + key, text + "图标", svg('<g fill="none" stroke="#c9c9c9" stroke-width="1.6" '
               'stroke-linecap="round" stroke-linejoin="round">' + icons[key] + '</g>'),
               20, y + 9, 18, 18, "sidebar")
        label("label_" + key, text, 44, y, 118, 36, bold=True, parent="sidebar")
        hit("nav_" + key, text, 14, y, 155, 36, "sidebar")
    label("tools_heading", "我的工具", 18, 202, 140, color=MUTED, size=8, parent="sidebar")
    label("settings_heading", "设置", 18, 332, 140, color=MUTED, size=8, parent="sidebar")
    vector("version_dot", "版本状态", svg('<circle cx="4" cy="4" r="4" fill="#59bb32"/>', 8, 8),
           17, 631, 8, 8, "sidebar")
    label("version", "已是最新版本 V25.10.22", 34, 623, 144, 24, color=MUTED, size=8, parent="sidebar")

    d.frame("titlebar", "自定义标题栏", 182, 0, 818, 40, BACKGROUND)
    label("top_name", "鹤鸢", 630, 6, 47, 30, bold=True, alignment="right_vcenter", parent="titlebar")
    avatar = avatar_image()
    d.add("picture_box", "top_avatar", "标题栏头像", 684, 10, 24, 24, parent="titlebar", image=avatar, border=False)
    d.frame("title_separator", "标题栏分隔线", 719, 9, 1, 23, "#777777", parent="titlebar")
    vector("minimize_icon", "最小化图标", svg('<path d="M7 12h10" stroke="#bdbdbd"/>'), 740, 10, 24, 24, "titlebar")
    vector("close_icon", "关闭图标", svg('<path d="m8 8 8 8m0-8-8 8" stroke="#bdbdbd"/>'), 784, 10, 24, 24, "titlebar")
    hit("minimize", "最小化", 729, 0, 44, 40, "titlebar")
    hit("close_window", "关闭", 773, 0, 45, 40, "titlebar")

    label("title", "个人中心", 200, 48, 500, 38, size=17, bold=True)
    d.add("picture_box", "avatar", "用户头像", 212, 104, 72, 72, image=avatar, border=False)
    label("nickname", "鹤鸢", 301, 104, 380, 28, size=14, bold=True)
    label("uid", "UID:  10000", 301, 130, 300, 23, size=10, color="#bbbbbb")
    vector("gender_badge", "性别标识", svg('<rect width="23" height="23" rx="4" fill="#242424"/>'
           '<g stroke="#53a19f" fill="none"><circle cx="9" cy="14" r="5"/><path d="m12 10 7-7m-6 0h6v6"/></g>', 23, 23),
           301, 154, 23, 23)
    vector("location_badge", "所在地背景", svg('<rect width="82" height="23" rx="4" fill="#242424"/>', 82, 23),
           332, 154, 82, 23)
    label("location", "安徽·滁州", 332, 154, 82, 23, size=8, bold=True, alignment="center")
    vector("edit_background", "修改资料背景", svg('<rect width="86" height="32" rx="5" fill="#282828"/>', 86, 32),
           865, 116, 86, 32)
    label("edit_caption", "修改资料", 865, 116, 86, 32, size=8, bold=True, alignment="center")
    hit("edit_profile", "修改资料", 865, 116, 86, 32)
    label("collection_heading", "我收藏的工具", 212, 200, 560, 24, size=8, color=MUTED)
    card = rendered_image(svg('<defs><linearGradient id="card"><stop stop-color="#7b6ce5"/>'
           '<stop offset="1" stop-color="#80aed0"/></linearGradient></defs>'
           '<rect width="144" height="144" rx="13" fill="url(#card)"/>'
           f'<g fill="#28c397">{BUNNY}</g>', 144, 144), 144, 144)
    for index in range(1, 4):
        x = 212 + (index - 1) * 153
        d.add("picture_box", f"tool_{index}", f"收藏工具{index}", x, 242, 144, 144,
              image=card, border=False, tool_tip=f"打开我喜欢的工具{index}")
        d.event(f"tool_{index}")
        label(f"tool_caption_{index}", f"我喜欢的工具{index}", x, 389, 144, 25,
              size=9, bold=True, alignment="center")
    d.focus("nav_home", "nav_profile", "nav_tools_one", "nav_tools_two", "nav_settings", "edit_profile", "minimize", "close_window")
    return d.finish()
