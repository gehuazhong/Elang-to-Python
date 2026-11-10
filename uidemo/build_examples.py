"""用当前设计器的模型、属性和导出器生成可继续编辑的桌面示例。"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QBuffer, QCoreApplication, QEvent, QIODevice
from PySide6.QtWidgets import QApplication

from codegen.publisher import HANDLERS, event_sources, export_project
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.commands.menus import add_menu, ensure_menu_bar, rename_menu
from core.events import event_bindings, set_event_enabled
from core.hierarchy import pages
from core.models import ProjectModel, Rect, new_project
from core.storage import atomic_write, commit_project, load_project
from runtime.application import configure_application
from runtime.builder import RuntimeTree
from resources.icons import ui_icon
from widgets.builtin import create_registry


INK = "#253332"
MUTED = "#697570"
PAPER = "#f5f6f2"
LINE = "#dde3dc"
GREEN = "#285c4b"
BLUE = "#315c91"


class Design:
    def __init__(self, name: str, width: int, height: int, background: str = PAPER):
        self.registry = create_registry()
        self.model = new_project(name)
        self.keys = {"main_window": self.model.root_id, "central_widget": self.model.central_id}
        self.set("main_window", geometry_width=width, geometry_height=height,
                 font_family="Microsoft YaHei UI", font_size=10, foreground_color=INK,
                 background_color=background)
        self.set("central_widget", background_color=background)

    def set(self, code: str, **properties):
        for key, value in properties.items():
            if key.startswith("geometry_"):
                key = key.replace("geometry_", "geometry.")
            self.model = set_property(self.model, self.registry, self.keys[code], key, value)
        return code

    def add(self, kind, code, name, x, y, width, height, *, parent="central_widget", **properties):
        if code in self.keys:
            raise ValueError(f"组件代码名称重复：{code}")
        used_names = {node.name for node in self.model.nodes.values()}
        original_name, number = name, 2
        while name in used_names:
            name, number = f"{original_name}{number}", number + 1
        self.model, key = create_node(self.model, self.registry, "builtin." + kind, x, y,
                                      parent_id=self.keys[parent])
        node = self.model.nodes[key]
        self.model = self.model.with_nodes({key: replace(node, name=name, code_name=code,
                                                        geometry=Rect(x, y, width, height))})
        self.keys[code] = key
        self.set(code, **properties)
        return code

    def label(self, code, text, x, y, width, height=28, *, size=10, bold=False, color=INK, **kwargs):
        return self.add("label", code, text.split("\n")[0][:24], x, y, width, height,
                        text=text, font_size=size, font_bold=bold, foreground_color=color, **kwargs)

    def frame(self, code, name, x, y, width, height, color, **kwargs):
        return self.add("frame", code, name, x, y, width, height, frame_shape="none",
                        content_left=0, content_top=0, content_right=0, content_bottom=0,
                        background_color=color, **kwargs)

    def button(self, code, text, x, y, width=104, *, primary=False, accent=GREEN, **kwargs):
        return self.add("button", code, text, x, y, width, 36, text=text,
                        background_color=accent if primary else "#ffffff",
                        foreground_color="#ffffff" if primary else INK, **kwargs)

    def event(self, code, event="clicked"):
        self.model = set_event_enabled(self.model, self.registry, self.keys[code], event, True)

    def focus(self, *codes):
        self.model = replace(self.model, data=self.model.data.changed(tab_order=[self.keys[code] for code in codes]))

    def tab_pages(self, code, *titles):
        result = []
        for index, (page, title) in enumerate(zip(pages(self.model, self.keys[code]), titles)):
            name = f"{code}_page_{index}"
            self.keys[name] = page.id
            self.model = self.model.with_nodes({page.id: replace(page, name=title, code_name=name)})
            self.set(name, text=title, background_color="#ffffff")
            result.append(name)
        return result

    def finish(self):
        self.registry.validate(self.model)
        compile_plan(self.model, self.registry, "示例设计")
        return self.model


def inventory():
    d = Design("青禾 · 库存管理台", 1040, 680)
    d.frame("sidebar", "侧栏", 0, 0, 196, 680, "#e7eee7")
    d.label("brand", "青禾仓库", 24, 32, 150, 38, size=22, bold=True, color=GREEN, parent="sidebar")
    d.label("brand_caption", "小团队的库存工作台", 24, 76, 156, color=MUTED, parent="sidebar")
    d.frame("nav_active", "当前模块", 16, 138, 164, 42, GREEN, parent="sidebar")
    d.label("nav_text", "01   库存总览", 16, 5, 145, 32, bold=True, color="#ffffff", parent="nav_active")
    d.label("warehouse_label", "当前仓库", 24, 220, 140, color=MUTED, parent="sidebar")
    d.label("warehouse", "杭州 · 一号仓", 24, 252, 154, bold=True, parent="sidebar")
    d.label("warehouse_note", "办公用品与设备\n统一登记，按需领用。", 24, 296, 148, 80,
            color=MUTED, word_wrap=True, parent="sidebar")
    d.label("sidebar_footer", "本地示例数据\n2026 / 11 / 07", 24, 598, 148, 52, color=MUTED, parent="sidebar")
    d.label("eyebrow", "WAREHOUSE / OVERVIEW", 228, 22, 510, color=MUTED, size=9)
    d.label("title", "库存总览", 228, 52, 510, 44, size=24, bold=True)
    d.label("subtitle", "快速找到物品，及时补足低库存。", 228, 103, 720, color=MUTED)
    stats = [("sku", "物品种类", "8", GREEN), ("stock", "在库数量", "406", INK),
             ("warning", "需要补货", "2", "#9a602b")]
    for index, (code, title, value, color) in enumerate(stats):
        x = 228 + index * 262
        d.frame(code + "_panel", title, x, 150, 246, 98, "#ffffff")
        d.label(code + "_label", title, 18, 10, 198, color=MUTED, parent=code + "_panel")
        d.label(code + "_value", value, 18, 40, 198, 46, size=25, bold=True, color=color, parent=code + "_panel")
    d.add("line_edit", "search", "搜索物品", 228, 274, 272, 36,
          placeholder_text="搜索 ID、名称或位置", background_color="#ffffff")
    d.add("combo_box", "category", "物品分类", 512, 274, 132, 36,
          items=["全部分类", "办公用品", "电子设备", "耗材"], background_color="#ffffff")
    d.add("check_box", "low_only", "仅看缺货", 658, 277, 132, 30, text="仅看低库存")
    d.button("search_button", "查询", 798, 274, 96, primary=True)
    d.button("reset_button", "重置", 906, 274, 100)
    rows = [
        ["1001", "A4 复印纸 / 500 张", "办公用品", "128", "A-01-01", "充足"],
        ["1002", "无线鼠标 / 石墨灰", "电子设备", "36", "B-02-04", "充足"],
        ["1003", "USB-C 扩展坞 / 六合一", "电子设备", "8", "B-02-06", "需补货"],
        ["1004", "黑色中性笔 / 0.5 mm", "办公用品", "96", "A-01-03", "充足"],
        ["1005", "标签纸 / 40 × 30 mm", "耗材", "12", "C-01-02", "充足"],
        ["1006", "笔记本支架 / 铝合金", "电子设备", "42", "B-03-01", "充足"],
        ["1007", "打印机墨盒 / 黑色", "耗材", "6", "C-02-01", "需补货"],
        ["1008", "牛皮纸档案袋 / A4", "办公用品", "78", "A-02-05", "充足"],
    ]
    d.add("super_list", "stock_list", "库存列表", 228, 326, 778, 284,
          table_data={"headers": ["ID", "物品名称 / 规格", "分类", "库存", "库位", "状态"],
                      "rows": rows, "column_widths": [62, 246, 106, 70, 116, 150]},
          row_height=31, sorting=True, alternating=False, background_color="#ffffff")
    d.label("result", "共 8 项 · 低库存阈值：10 件", 228, 620, 460, color=MUTED, size=9)
    d.label("selection", "选择一行查看物品信息", 228, 647, 778, 24, color=MUTED, size=9)
    for code, event in (("search", "textChanged"), ("category", "currentIndexChanged"),
                        ("low_only", "toggled"), ("search_button", "clicked"),
                        ("reset_button", "clicked"), ("stock_list", "selection_changed")):
        d.event(code, event)
    d.focus("search", "category", "low_only", "search_button", "reset_button", "stock_list")
    return d.finish()


def tasks():
    d = Design("拾光 · 任务下载中心", 1000, 660, "#f3f5f8")
    d.frame("header", "标题区域", 0, 0, 1000, 122, "#e5edf8")
    d.label("eyebrow", "TRANSFER / LOCAL DEMO", 32, 16, 700, size=9, color=BLUE, parent="header")
    d.label("title", "让文件，有序到达。", 32, 46, 760, 46, size=26, bold=True, color="#263f62", parent="header")
    d.label("queue_title", "下载队列", 32, 144, 340, 34, size=16, bold=True)
    d.label("queue_count", "4 个任务  /  1 个已完成", 662, 149, 306, color=MUTED, alignment="right_vcenter")
    d.add("line_edit", "task_name", "新任务名称", 32, 194, 542, 36,
          placeholder_text="输入演示任务名称，例如：产品图册.pdf", background_color="#ffffff")
    d.button("add_task", "添加任务", 588, 194, 116, primary=True, accent=BLUE)
    d.button("toggle_task", "开始 / 暂停", 716, 194, 126)
    d.button("clear_done", "清理已完成", 854, 194, 114)
    d.add("table_widget", "task_table", "任务队列", 32, 248, 936, 230,
          table_data={"headers": ["ID", "文件名称", "大小", "进度", "状态"],
                      "column_widths": [62, 436, 140, 116, 178], "rows": [
                          ["01", "品牌素材包.zip", "128 MB", "64%", "已暂停"],
                          ["02", "产品使用手册.pdf", "8 MB", "100%", "已完成"],
                          ["03", "产品展示视频.mp4", "256 MB", "0%", "等待中"],
                          ["04", "活动宣传图片.zip", "48 MB", "0%", "等待中"]]},
          show_vertical_header=False, show_grid=False, word_wrap=False,
          alternating_rows=False, background_color="#ffffff")
    d.frame("progress_panel", "当前任务区域", 32, 496, 936, 106, "#ffffff")
    d.label("active_task", "品牌素材包.zip", 18, 10, 640, 28, bold=True, parent="progress_panel")
    d.label("progress_caption", "已暂停 · 点击“开始 / 暂停”继续", 18, 42, 550, 24,
            size=9, color=MUTED, parent="progress_panel")
    d.add("progress_bar", "progress", "任务进度", 18, 74, 900, 18,
          parent="progress_panel", value=64, text_visible=False)
    d.label("notice", "本地模拟任务；不会连接网络或下载文件。", 32, 616, 936, color=MUTED, size=9)
    for code, event in (("add_task", "clicked"), ("task_name", "returnPressed"),
                        ("toggle_task", "clicked"), ("clear_done", "clicked"),
                        ("task_table", "itemSelectionChanged")):
        d.event(code, event)
    d.focus("task_name", "add_task", "toggle_task", "clear_done", "task_table")
    return d.finish()


def login():
    d = Design("栖木 · 账号登录", 900, 590, "#ffffff")
    d.frame("brand_panel", "品牌区域", 0, 0, 360, 590, "#243e36")
    d.label("brand", "栖木 / WORKSPACE", 32, 36, 300, 32, size=12, bold=True,
            color="#dbe9da", parent="brand_panel")
    d.label("brand_title", "专注眼前，\n让工作归位。", 32, 174, 302, 120,
            size=28, bold=True, color="#ffffff", parent="brand_panel")
    d.label("brand_note", "一个清晰的入口，\n开始今天的工作。", 32, 330, 292, 70,
            size=12, color="#c3d1c5", parent="brand_panel")
    d.frame("accent", "品牌装饰线", 32, 466, 64, 4, "#c7d5a5", parent="brand_panel")
    d.label("brand_footer", "桌面工作空间  /  UI DEMO 03", 32, 520, 304, size=9,
            color="#c3d1c5", parent="brand_panel")
    d.label("eyebrow", "欢迎回来", 416, 40, 428, color=MUTED)
    d.label("title", "登录你的工作空间", 416, 76, 428, 48, size=23, bold=True)
    d.label("subtitle", "填写演示账号，体验完整的表单交互。", 416, 135, 430, color=MUTED)
    d.label("account_label", "账号", 416, 190, 380, bold=True)
    d.add("line_edit", "account", "账号输入", 416, 224, 428, 40, placeholder_text="请输入账号", max_length=40)
    d.label("password_label", "密码", 416, 282, 380, bold=True)
    d.add("line_edit", "password", "密码输入", 416, 316, 428, 40,
          placeholder_text="请输入演示密码", echo_mode="password", clear_button=False, max_length=80)
    d.add("check_box", "show_password", "显示密码", 416, 371, 178, 28, text="显示密码")
    d.button("fill_demo", "填入演示账号", 678, 367, 166)
    d.button("login_button", "登录工作空间", 416, 420, 428, primary=True)
    d.label("message", "演示账号：demo    密码：demo123", 416, 470, 428, 56,
            color=MUTED, word_wrap=True, size=9)
    d.label("footer", "仅演示本地校验，不会保存或发送输入内容。", 416, 543, 438, size=9, color=MUTED)
    for code, event in (("show_password", "toggled"), ("fill_demo", "clicked"),
                        ("login_button", "clicked"), ("password", "returnPressed")):
        d.event(code, event)
    d.focus("account", "password", "show_password", "fill_demo", "login_button")
    return d.finish()


def settings():
    d = Design("方寸 · 应用设置", 1000, 670, "#f6f3ec")
    d.label("eyebrow", "PREFERENCES / YOUR SPACE", 32, 20, 740, size=9, color=MUTED)
    d.label("title", "把工作台调成你的习惯", 32, 52, 870, 48, size=24, bold=True)
    d.label("subtitle", "一个设置页面，管理常用偏好与通知。", 32, 108, 874, color=MUTED)
    d.add("tab_widget", "settings_tabs", "设置分类", 32, 156, 936, 380)
    general, notifications = d.tab_pages("settings_tabs", "  常规偏好  ", "  通知与计划  ")
    d.label("profile_title", "工作空间", 24, 22, 540, 30, size=14, bold=True, parent=general)
    d.label("workspace_label", "空间名称", 24, 74, 170, parent=general)
    d.add("line_edit", "workspace_name", "空间名称", 198, 70, 398, 36,
          text="我的工作空间", placeholder_text="输入空间名称", parent=general)
    d.label("language_label", "界面语言", 24, 126, 170, parent=general)
    d.add("combo_box", "language", "界面语言", 198, 122, 398, 36,
          items=["简体中文", "English", "繁體中文"], parent=general)
    d.label("retention_label", "历史保留", 24, 178, 170, parent=general)
    d.add("spin_box", "retention", "历史保留天数", 198, 174, 180, 36,
          minimum=1, maximum=365, value=30, suffix=" 天", parent=general)
    d.add("check_box", "auto_save", "自动保存偏好", 24, 236, 548, 30,
          text="编辑时自动保存草稿", check_state="checked", parent=general)
    d.label("general_note", "语言和自动保存项仅展示设置值，不改变演示程序行为。", 24, 292, 558, 46,
            size=9, color=MUTED, word_wrap=True, parent=general)
    d.frame("general_aside", "常规设置说明", 634, 24, 274, 296, "#f2f3ec", parent=general)
    d.label("aside_index", "01 / GENERAL", 20, 18, 230, color=GREEN, size=9, parent="general_aside")
    d.label("aside_title", "少一点重复，\n多一点顺手。", 20, 64, 230, 84,
            size=18, bold=True, parent="general_aside")
    d.label("aside_note", "试着修改空间名称，\n再点击下方“应用设置”。\n\n演示设置仅在本次运行有效。", 20, 178, 234, 100,
            color=MUTED, size=9, parent="general_aside")
    d.label("notifications_title", "提醒与定时计划", 24, 22, 530, 30, size=14, bold=True, parent=notifications)
    d.add("check_box", "notifications", "启用通知", 24, 72, 526, 30,
          text="启用桌面提醒", check_state="checked", parent=notifications)
    d.label("volume_label", "提示音量", 24, 126, 170, parent=notifications)
    d.add("slider", "volume", "提示音量", 198, 126, 338, 28, value=60, parent=notifications)
    d.label("volume_value", "60%", 550, 126, 60, parent=notifications)
    d.label("schedule_label", "计划日期", 24, 180, 170, parent=notifications)
    d.add("date_edit", "schedule_date", "计划日期", 198, 176, 398, 36,
          value="2026-11-09", display_format="yyyy-MM-dd", parent=notifications)
    d.add("check_box", "quiet_mode", "专注时静音", 24, 236, 546, 30,
          text="专注模式下保持静音", check_state="checked", parent=notifications)
    d.label("notification_note", "这里展示通知配置，不创建系统通知或后台计划。", 24, 292, 558, 46,
            size=9, color=MUTED, word_wrap=True, parent=notifications)
    d.frame("notification_aside", "通知设置说明", 634, 24, 274, 296, "#edf1f7", parent=notifications)
    d.label("notification_index", "02 / NOTIFICATIONS", 20, 18, 236, size=9, color=BLUE, parent="notification_aside")
    d.label("notification_heading", "重要的事，\n在合适时提醒。", 20, 64, 236, 84,
            size=18, bold=True, parent="notification_aside")
    d.label("notification_help", "关闭桌面提醒后，\n音量与静音选项自动禁用。\n\n拖动滑块可查看音量数值。", 20, 178, 236, 100,
            size=9, color=MUTED, parent="notification_aside")
    d.label("settings_summary", "当前：我的工作空间 · 简体中文 · 历史 30 天 · 提醒开启", 32, 552, 936, 34, color=MUTED, size=9)
    d.button("restore", "恢复默认", 32, 610, 116)
    d.label("settings_message", "修改后点击“应用设置”查看结果。", 168, 610, 638, 36, color=MUTED, size=9)
    d.button("apply", "应用设置", 840, 610, 128, primary=True)
    for code, event in (("notifications", "toggled"), ("volume", "valueChanged"),
                        ("restore", "clicked"), ("apply", "clicked")):
        d.event(code, event)
    d.focus("settings_tabs", "workspace_name", "language", "retention", "auto_save", "notifications",
            "volume", "schedule_date", "quiet_mode", "restore", "apply")
    return d.finish()


def menus():
    d = Design("菜单编辑示例", 880, 600)
    d.label("eyebrow", "菜单与事件", 36, 26, 800, 24, size=9, color=MUTED)
    d.label("title", "我的项目工作台", 36, 60, 800, 46, size=24, bold=True)
    d.label("intro", "文件、视图、帮助菜单可直接操作，也可以使用 Ctrl+N、Ctrl+G。", 36, 116, 800, 32, color=MUTED)
    d.frame("content", "内容区", 36, 180, 808, 246, "#ffffff")
    d.label("content_title", "从菜单开始操作", 24, 24, 748, 34, size=16, bold=True, parent="content")
    d.label("detail", "文件 → 新建项目：更新下方状态\n文件 → 最近项目：体验三级菜单\n视图 → 显示说明：切换本区内容\n禁止操作不可点击；隐藏操作不会显示", 24, 82, 748, 128,
            color=MUTED, parent="content")
    d.label("menu_message", "就绪。请使用窗口上方菜单。", 36, 458, 808, 42, color=GREEN)
    d.model, bar = ensure_menu_bar(d.model, d.registry)
    d.keys["menu_bar"] = bar
    for code, parent, title, values in (
        ("menu_file", "menu_bar", "文件(&F)", {}),
        ("menu_new", "menu_file", "新建项目(&N)", {"shortcut": "Ctrl+N"}),
        ("menu_recent", "menu_file", "最近项目(&R)", {}),
        ("menu_recent_inventory", "menu_recent", "库存管理台", {}),
        ("menu_recent_tasks", "menu_recent", "任务下载中心", {}),
        ("menu_separator", "menu_file", "-", {"separator": True}),
        ("menu_disabled", "menu_file", "禁止操作", {"enabled": False}),
        ("menu_hidden", "menu_file", "隐藏操作", {"visible": False}),
        ("menu_exit", "menu_file", "退出(&X)", {"shortcut": "Ctrl+Q"}),
        ("menu_view", "menu_bar", "视图(&V)", {}),
        ("menu_details", "menu_view", "显示说明(&G)", {"checked": True, "shortcut": "Ctrl+G"}),
        ("menu_help", "menu_bar", "帮助(&H)", {}),
        ("menu_about", "menu_help", "关于菜单示例", {"shortcut": "F1"}),
    ):
        d.model, key = add_menu(d.model, d.registry, d.keys[parent], separator=values.get("separator", False))
        d.model = rename_menu(d.model, key, "文件菜单分隔线" if title == "-" else title, code)
        d.keys[code] = key
        d.set(code, text=title, **values)
    for code in ("menu_new", "menu_recent_inventory", "menu_recent_tasks", "menu_exit", "menu_details", "menu_about"):
        d.event(code)
    return d.finish()


def text_inputs():
    d = Design("文本与输入组件", 1000, 690)
    d.label("eyebrow", "TEXT / INPUT", 32, 22, 900, 24, size=9, color=MUTED)
    d.label("title", "一页文字，从编辑到预览", 32, 54, 900, 46, size=24, bold=True)
    d.label("intro", "输入内容、选择字体，再用自己的快捷键保存本次草稿。", 32, 106, 920, 28, color=MUTED)
    d.label("font_label", "字体", 32, 151, 48)
    d.add("font_combo_box", "font_picker", "正文字体", 82, 148, 294, 34,
          current_font="Microsoft YaHei UI", editable=False)
    d.label("size_label", "字号", 398, 151, 48)
    d.add("spin_box", "font_size", "正文字号", 450, 148, 130, 34, minimum=8, maximum=36, value=12)
    d.label("preview_title", "即时预览", 604, 151, 364, 28, bold=True)
    d.add("rich_text_edit", "editor", "正文编辑", 32, 196, 548, 324, text_format="rich",
          text="<h2>写下今天的想法</h2><p>这是可编辑的<b>富文本</b>。试着增加一行内容，右侧预览会同步更新。</p><p>中文、数字与格式都可以保留。</p>",
          document_margin=16, font_size=12, background_color="#ffffff")
    d.add("text_browser", "reader", "正文预览", 604, 196, 364, 188, open_links=False,
          text='<h3>预览区域</h3><p>运行导出示例后，内容会与左侧同步。</p><p><a href="demo:restore">恢复示例内容</a></p>',
          document_margin=12, background_color="#ffffff")
    d.add("group_box", "options", "编辑选项", 604, 404, 364, 116, text="启用编辑选项",
          checkable=True, checked=True, content_left=12, content_top=26, content_right=12, content_bottom=8)
    d.add("check_box", "read_only", "只读选项", 0, 4, 332, 28, parent="options", text="只读浏览（禁止修改正文）")
    d.label("option_note", "取消组选中后可继续编辑。", 0, 38, 332, 28, color=MUTED, size=9, parent="options")
    d.label("shortcut_label", "保存快捷键", 32, 542, 126, 28)
    d.add("key_sequence_edit", "shortcut_input", "快捷键录入", 154, 538, 240, 36, key_sequence="Ctrl+Shift+S")
    d.button("apply_shortcut", "应用快捷键", 408, 538, 172)
    buffer = QBuffer()
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly) or not ui_icon("save", "#ffffff").pixmap(32, 32).save(buffer, "PNG"):
        raise RuntimeError("无法准备示例按钮图标。")
    d.button("save_draft", "保存草稿", 804, 538, 164, primary=True, shortcut="Ctrl+S",
             icon=bytes(buffer.data().toBase64()).decode("ascii"), icon_width=20, icon_height=20)
    d.label("help_link", '<a href="demo:help">查看操作说明</a>', 604, 542, 184, 28, text_format="rich")
    d.label("statistics", "字数统计将在输入时更新。", 32, 592, 548, 28, color=MUTED, size=9)
    d.label("message", "初始保存快捷键：Ctrl+S。草稿仅保存在本次运行中。", 32, 626, 936, 32, color=GREEN, size=9)
    for code, event in (("editor", "textChanged"), ("font_picker", "currentFontChanged"),
                        ("font_size", "valueChanged"), ("reader", "anchorClicked"), ("help_link", "linkActivated"),
                        ("options", "toggled"), ("read_only", "toggled"), ("shortcut_input", "keySequenceChanged"),
                        ("apply_shortcut", "clicked"), ("save_draft", "clicked")):
        d.event(code, event)
    d.focus("font_picker", "font_size", "editor", "reader", "options", "read_only",
            "shortcut_input", "apply_shortcut", "save_draft", "help_link")
    return d.finish()


from uidemo.profile_example import profile


EXAMPLES = (
    ("01_库存管理台", "库存管理台", inventory, "inventory_demo"),
    ("02_任务下载中心", "任务下载中心", tasks, "tasks_demo"),
    ("03_账号登录", "账号登录", login, "login_demo"),
    ("04_应用设置", "应用设置", settings, "settings_demo"),
    ("05_菜单编辑示例", "菜单编辑示例", menus, "menus_demo"),
    ("06_文本与输入组件", "文本与输入组件", text_inputs, "text_inputs_demo"),
    ("07_兔子工具个人中心", "兔子工具个人中心", profile, "profile_demo"),
)


def install_behavior(model, registry, target, module_name):
    logic = target / (module_name + ".py")
    if not logic.exists():
        atomic_write(logic, (Path(__file__).parent / "logic" / (module_name + ".py")).read_bytes())
    handlers = target / "handlers.py"
    if handlers.read_bytes() == HANDLERS.encode("utf-8"):
        source = ('"""演示初始化；再次导出会保留本文件。"""\n\n'
                  f"from {module_name} import initialize\n\n\n"
                  "def connect_events(window):\n    initialize(window)\n")
        atomic_write(handlers, source.encode("utf-8"))
    original = event_sources(model, registry)
    for binding in event_bindings(model, registry):
        name = binding["handler"]
        path = target / "event_handlers" / (name + ".py")
        if path.read_bytes() != original[name + ".py"]:
            continue
        source = ('"""演示事件；再次导出会保留本文件。"""\n\n'
                  f"from {module_name} import dispatch\n\n\n"
                  f"def {name}(window, *arguments):\n"
                  f"    return dispatch(window, {binding['control']!r}, {binding['key']!r}, arguments)\n")
        atomic_write(path, source.encode("utf-8"))


def render(app, registry, model, path):
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "示例截图"))
        tree.root.show()
        app.processEvents()
        if not tree.root.grab().save(str(path)):
            raise RuntimeError("无法写入预览图。")
        for node in model.nodes.values():
            if node.type_id == "builtin.tab_widget":
                tabs = tree.widgets[node.id]
                for index in range(1, len(tabs.pages)):
                    tabs.set_current_page(index)
                    app.processEvents()
                    if not tree.root.grab().save(str(path.with_stem(path.stem + f"_第{index + 1}页"))):
                        raise RuntimeError("无法写入分页预览图。")
    finally:
        tree.dispose()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent)
    parser.add_argument("--only", type=int, choices=range(1, len(EXAMPLES) + 1), help="仅生成指定编号，不改其他示例")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    configure_application(app)
    registry = create_registry()
    output = args.output.resolve()
    entries = []
    for number, (directory, title, factory, module_name) in enumerate(EXAMPLES, 1):
        if args.only is not None and args.only != number:
            continue
        folder = output / directory
        project = folder / (title + ".uipro")
        if project.exists():
            model = load_project(project).model
        else:
            model = factory()
            commit_project(project, model, expected_token=None)
        registry.validate(model)
        exported = folder / "Python导出"
        export_project(model, registry, exported)
        install_behavior(model, registry, exported, module_name)
        export_project(model, registry, exported)
        render(app, registry, model, folder / "预览.png")
        entries.append({"名称": title, "设计文件": str(project.relative_to(output)),
                        "运行入口": str((exported / "main.py").relative_to(output)),
                        "组件数": len(model.nodes), "已勾选事件数": len(event_bindings(model, registry))})
        print(f"已生成：{project}", flush=True)
    if args.only is not None and (output / "示例清单.json").exists():
        existing = json.loads((output / "示例清单.json").read_text(encoding="utf-8"))
        names = {entry["名称"] for entry in entries}
        entries = [entry for entry in existing if entry["名称"] not in names] + entries
    atomic_write(output / "示例清单.json", json.dumps(entries, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
