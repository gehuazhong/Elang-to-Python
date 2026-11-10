"""Create a layout/container example and capture it in the VS Code workbench."""

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from PySide6.QtCore import QSettings, QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from app.bootstrap import initialize
    from app.main_window import MainWindow
    from core.models import new_project
    from core.commands.nodes import create_node, set_property
    from core.commands.pages import add_page
    from core.hierarchy import pages
    from layout.containers import managed_child
    from core.storage import commit_project
    from widgets.builtin import create_registry
    app = QApplication([])
    initialize(app, configure_logging=False)
    registry = create_registry()
    model = new_project("自动布局与高级容器")

    def change(key, **values):
        nonlocal model
        for name, value in values.items():
            model = set_property(model, registry, key, name, value)

    def create(kind, x, y, width, height, parent=None, **values):
        nonlocal model
        model, key = create_node(model, registry, "builtin." + kind, x, y, parent_id=parent)
        if model.nodes[key].geometry is not None and not managed_child(model, key):
            change(key, **{"geometry.width": width, "geometry.height": height})
        change(key, **values)
        return key

    change(model.root_id, window_title="自动布局与高级容器", **{"geometry.width": 1080, "geometry.height": 680})
    dock = create("dock_widget", 0, 0, 0, 0, title="组件目录", dock_width=190)
    create("tree_view", 8, 8, 165, 550, dock,
           tree_data=[{"text": "项目", "children": [{"text": "自动布局", "children": []},
                        {"text": "模型视图", "children": []}, {"text": "多文档窗口", "children": []}]}])
    tab = create("tab_widget", 16, 16, 830, 625)
    first, second = pages(model, tab)
    model, third = add_page(model, registry, tab)
    change(first.id, text="自动布局")
    change(second.id, text="页面与滚动")
    change(third, text="多文档")
    create("label", 16, 12, 740, 32, first.id, text="布局按内容排列，窗口中保持统一间距", font_size=14)
    horizontal = create("horizontal_layout", 16, 56, 770, 64, first.id)
    create("label", 0, 0, 90, 32, horizontal, text="关键词")
    create("line_edit", 0, 0, 250, 32, horizontal, placeholder_text="输入名称搜索", layout_stretch=1)
    create("button", 0, 0, 100, 32, horizontal, text="查询")
    grid = create("grid_layout", 16, 136, 770, 200, first.id, columns=2)
    create("list_view", 0, 0, 300, 180, grid, items=["已接入 72 类组件", "中文属性与事件", "保存、复制与撤销", "独立 Python 导出"])
    create("table_view", 0, 0, 300, 180, grid, table_data={"headers": ["控件", "状态"],
           "rows": [["模型视图", "可编辑"], ["自动布局", "已启用"], ["原生预览", "可运行"]]}, editable=True)
    form = create("form_layout", 16, 352, 770, 130, first.id)
    create("label", 0, 0, 90, 32, form, text="项目名称")
    create("line_edit", 0, 0, 240, 32, form, text="界面示例")
    create("label", 0, 0, 90, 32, form, text="负责人")
    create("line_edit", 0, 0, 240, 32, form, placeholder_text="请输入姓名")
    footer = create("horizontal_layout", 16, 498, 770, 60, first.id)
    create("spacer", 0, 0, 30, 30, footer, layout_stretch=1)
    create("dialog_button_box", 0, 0, 260, 36, footer)
    box = create("tool_box", 16, 16, 365, 535, second.id)
    a, b = pages(model, box)
    change(a.id, text="列表模型")
    change(b.id, text="树形模型")
    create("list_view", 8, 8, 325, 420, a.id, items=["双击页头切换", "选择对象树中的页面", "右键添加或删除页面"])
    create("tree_view", 8, 8, 325, 420, b.id)
    scroll = create("scroll_area", 400, 16, 385, 535, second.id, content_width=350, content_height=820)
    create("table_view", 8, 8, 330, 780, scroll, table_data={"headers": ["行号", "说明"],
           "rows": [[str(i), "滚动查看内容"] for i in range(1, 31)]})
    mdi = create("mdi_area", 16, 16, 770, 540, third)
    left = create("mdi_subwindow", 16, 24, 345, 410, mdi, title="数据窗口")
    right = create("mdi_subwindow", 390, 70, 345, 410, mdi, title="预览窗口")
    create("table_view", 8, 8, 305, 340, left)
    create("svg_widget", 8, 8, 305, 300, right)
    output = ROOT / "reports/components-completion"
    output.mkdir(parents=True, exist_ok=True)
    example = ROOT / "examples/自动布局与高级容器.uipro"
    if not example.exists():
        commit_project(example, model, expected_token=None)
    with tempfile.TemporaryDirectory(prefix="uiplay_components_") as temporary:
        settings = QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat)
        window = MainWindow(registry, settings=settings, enable_recovery=False, persist_settings=False)
        try:
            window.resize(1500, 940)
            window.show()
            document = window.open_path(example)
            tab_id = next(node.id for node in document.model.nodes.values() if node.type_id == "builtin.tab_widget")
            layout_id = next(node.id for node in document.model.nodes.values() if node.type_id == "builtin.grid_layout")
            for index, name in enumerate(("layouts", "pages-scroll", "mdi")):
                document.execute("查看示例页面", lambda current, i=index: set_property(current, registry, tab_id, "current_index", i))
                document.select(layout_id if index == 0 else tab_id)
                window.page.canvas.fit_to_window()
                QTest.qWait(150)
                assert window.grab().save(str(output / ("workbench-" + name + ".png")))
            print(str(example))
        finally:
            window.discard_all_for_test()
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


if __name__ == "__main__":
    main()
