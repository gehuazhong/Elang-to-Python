"""Generate the property audit and example; verify Windows preview and isolated export."""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.storage import atomic_write, commit_project, load_project
from runtime.builder import RuntimeTree, verify_registry
from uidemo.build_examples import Design
from widgets.builtin import create_registry
from widgets.support import support_markdown


COMMON_KEYS = {"cursor_shape", "focus_policy", "mouse_tracking", "accessible_name", "accessible_description",
               "whats_this", "tool_tip_duration", "style_sheet", "size_policy_horizontal", "size_policy_vertical"}


def audit(registry, output):
    baseline = create_registry(complete=False)
    rows = []
    for key, spec in registry.specs.items():
        before = {prop.key: prop for prop in baseline.specs[key].properties}
        added = [{"key": prop.key, "label": prop.label, "group": prop.group, "type": prop.value_type,
                  "qt_property": prop.qt_name} for prop in spec.properties if prop.key not in before]
        changed = [{"key": prop.key, "label": prop.label} for prop in spec.properties
                   if prop.key in before and prop != before[prop.key]]
        rows.append({"type_id": key, "label": spec.label, "qt_class": spec.qt_class, "toolbox": spec.toolbox,
                     "before": len(before), "after": len(spec.properties), "added": added, "changed": changed})
    report = {"registered_types": len(rows), "toolbox_types": sum(row["toolbox"] for row in rows),
              "before": sum(row["before"] for row in rows), "after": sum(row["after"] for row in rows),
              "added_property_entries": sum(len(row["added"]) for row in rows), "components": rows}
    atomic_write(output / "audit.json", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))
    lines = ["# 组件属性审计", "", "本轮核对注册表中的全部组件，补齐适合在设计器内配置、保存和导出的常用属性。", "",
             f"注册表共 {report['registered_types']} 项，其中组件箱 {report['toolbox_types']} 类。属性项由 {report['before']} 增至 {report['after']}，新增 {report['added_property_entries']} 个组件属性项。",
             "同一个公共属性在不同组件中分别计数，因此新增项数不等于独立 Qt 属性或功能数。", "",
             "## 查找和使用", "",
             "选中组件，在右侧属性面板搜索中文名称。表格和树的标题设置主要位于“表头”，列表排列位于“外观”，自动布局位于“布局”，对话框位于“对话框”。已有属性保留原分组及稳定字段。",
             "普通表格沿用“外观 → 显示列标题”和“显示行号”，分别控制水平、垂直表头；模型表格使用“表头 → 显示水平表头”和“显示垂直表头”。",
             "鼠标指针位于“外观”，键盘焦点方式位于“行为”，自定义样式、无障碍名称和说明位于“高级”。“行为”和“高级”默认折叠，可展开或搜索。",
             "可视子组件的水平、垂直尺寸策略位于“布局”，加入自动布局后决定空间分配。", "",
             "打开 [组件属性补全示例](../examples/组件属性补全示例.uipro) 可对照表头隐藏、排序、树折叠、列表网格、输入掩码、多段快捷键和表单换行。",
             "示例和检查脚本不会覆盖已有同名示例；重新运行时加载当前文件。", "",
             "## 公共属性", "",
             "适用的可视组件增加鼠标指针、焦点方式、鼠标移动跟踪、提示持续时间、帮助说明、无障碍名称和说明、自定义 QSS；可视子组件另有水平和垂直尺寸策略。",
             "非可视服务、菜单项和布局对象按各自类型提供属性，未生硬套用 QWidget 公共属性。", "",
             "## 逐组件结果", "",
             "下表的新增项数包含公共属性；专属列省略上述公共属性。完整键名、中文名、分组和原生映射见 [audit.json](../reports/property-completion/audit.json)，全部现有属性见 [组件支持矩阵](组件支持矩阵.md)。", "",
             "| 组件 | Qt 类 | 原属性数 | 现属性数 | 新增数 | 新增专属属性 |",
             "| --- | --- | ---: | ---: | ---: | --- |"]
    for row in rows:
        labels = "、".join(prop["label"] for prop in row["added"] if prop["key"] not in COMMON_KEYS) or "无专属新增"
        lines.append(f"| {row['label']} | {row['qt_class']} | {row['before']} | {row['after']} | {len(row['added'])} | {labels} |")
    lines += ["", "## 既有属性扩展与组合行为", "",
              "标签对齐扩展为九个位置。快捷键编辑框支持一至四段组合键；按钮和菜单快捷键仍使用单段，缩短录入长度时不会静默截断已有值。",
              "输入掩码只约束运行时显示，撤销后恢复原文。表格填充数据时暂停排序，避免单元格被写入错误行。明确指定的末列宽度优先于“末列填满”；选择拉伸或适应内容模式时，由所选模式计算列宽。",
              "列表网格宽、高可独立编辑，零值轴采用自动尺寸。表单及网格的独立间距设为 -1 时沿用总间距。独立页签栏单页自动隐藏会在设计画布、预览和导出同步生效。",
              "自定义 QSS 直接作用于组件，优先于通用外观生成的样式；清空后恢复原有外观设置。工具条允许移动和浮动仍受其挂接位置及运行容器约束。",
              "网页设置可更新已加载的页面，只有内容源变更才重新加载；OpenGL 和 RHI 的采样数变化会重建图形表面。SVG 关闭动画后，隐藏再显示或切换页面也会保留设置。", "",
              "## 范围", "",
              "这次补全覆盖常用设计属性，并非 Qt 全部 API。只读运行状态、依赖外部对象的 model/delegate、图形上下文、选择模型和由内容自动派生的行列数不作为静态属性编辑。",
              "超级列表框继续提供报表式多列；图标网格使用列表框或模型列表的“显示方式”。原生系统对话框的外观与平台支持相关；设计时不打开系统对话框、不运行 Chromium 或 GPU。",
              "旧项目不需要迁移，缺省字段由注册表补默认值；不会为补属性主动重写原项目。", "",
              "## 验证", "",
              "运行 `python -X utf8 scripts/check_completed_properties.py` 更新审计、示例和 Windows 截图，同时用 `python -I` 在临时目录验证独立导出。",
              "组合行为专项测试为 `tests/test_property_completion.py`。最终回归、图形实机结果及源码指纹见 [验证记录](../reports/property-completion/README.md)。", ""]
    atomic_write(ROOT / "docs/组件属性审计.md", "\n".join(lines).encode("utf-8"))
    atomic_write(ROOT / "docs/组件支持矩阵.md", support_markdown(registry).encode("utf-8"))
    return {key: value for key, value in report.items() if key != "components"}


def example():
    d = Design("组件属性 · 对照示例", 1080, 756, "#f4f5f7")
    d.label("title", "组件属性对照", 24, 14, 1000, 38, size=20, bold=True)
    d.label("intro", "在对象树选择组件，再在属性面板搜索：表头、网格、掩码、换行。", 24, 52, 1020, 26, color="#68717d")
    data = {"headers": ["编号", "名称", "状态"], "rows": [["03", "字体组合框", "已补齐"],
            ["01", "表格组件", "可排序"], ["02", "模型视图", "可调整"]], "column_widths": [74, 230, 150]}
    d.label("table_caption", "表格：隐藏行号，行高 40，点击表头排序", 24, 88, 490, 28, bold=True)
    d.add("table_widget", "table", "表格属性对照", 24, 122, 490, 176, table_data=data,
          show_vertical_header=False, row_height=40, sorting=True, header_movable=True)
    d.label("model_caption", "模型表格：隐藏两侧表头，虚线网格", 544, 88, 512, 28, bold=True)
    d.add("table_view", "model_table", "模型表格属性对照", 544, 122, 512, 176, table_data=data,
          show_horizontal_header=False, show_vertical_header=False, row_height=40, grid_style="dash")
    nodes = [{"text": "界面组件", "children": [{"text": "输入与显示", "children": []},
             {"text": "列表与表格", "children": []}]}, {"text": "布局与容器", "children": []}]
    d.label("tree_caption", "树形框：隐藏表头", 24, 318, 240, 28, bold=True)
    d.add("tree_widget", "tree", "隐藏表头树", 24, 354, 234, 168,
          tree_data=nodes, header_hidden=True, indentation=26, animated=True)
    d.label("tree_model_caption", "模型树：初始折叠", 280, 318, 240, 28, bold=True)
    d.add("tree_view", "model_tree", "折叠模型树", 280, 354, 234, 168,
          tree_data=nodes, header_text="组件分类", expanded=False, indentation=26)
    d.label("list_caption", "列表框：网格排列，每格 112 × 56", 544, 318, 510, 28, bold=True)
    d.add("list_widget", "list", "网格列表", 544, 354, 512, 168,
          items=["首页", "文档", "图片", "设置", "工具", "帮助"], view_mode="icons",
          grid_width=112, grid_height=56, list_wrapping="yes", list_resize_mode="adjust")
    d.label("input_caption", "输入格式与多段快捷键", 24, 542, 490, 28, bold=True)
    d.label("mask_label", "输入掩码", 24, 588, 102, 30)
    d.add("line_edit", "mask", "输入掩码示例", 132, 588, 244, 32, text="123456", input_mask="000-000;_")
    d.label("sequence_label", "两段快捷键", 24, 636, 102, 30)
    d.add("key_sequence_edit", "sequence", "两段快捷键示例", 132, 636, 244, 32,
          maximum_sequence_length=2, key_sequence="Ctrl+K, Ctrl+C")
    d.label("lcd_label", "十六进制", 396, 578, 118, 30)
    d.add("lcd_number", "lcd", "十六进制示例", 396, 616, 118, 52, value=255, digit_count=3, number_mode="hex")
    d.label("form_caption", "表单布局：标签与字段分行，垂直间距 12", 544, 542, 512, 28, bold=True)
    d.add("form_layout", "form", "换行表单", 544, 578, 512, 112,
          row_wrap_policy="all_rows", vertical_spacing=12, horizontal_spacing=20, layout_alignment="top_left")
    d.label("form_label", "项目名称", 0, 0, 160, 28, parent="form")
    d.add("line_edit", "form_input", "表单输入", 0, 0, 370, 32, parent="form", placeholder_text="字段自动排列在标签下方")
    d.label("footer", "属性修改支持保存、复制和撤销，并同步到独立预览与 Python 导出。", 24, 714, 1030, 26, color="#68717d")
    return d.finish()


def main():
    app = QApplication([])
    initialize(app, configure_logging=False)
    registry = create_registry()
    verify_registry(registry)
    output = ROOT / "reports/property-completion"
    output.mkdir(parents=True, exist_ok=True)
    result = {"platform": app.platformName(), "audit": audit(registry, output)}
    path = ROOT / "examples/组件属性补全示例.uipro"
    if not path.exists():
        commit_project(path, example(), expected_token=None)
    model = load_project(path).model
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "属性对照"))
        controls = {node.code_name: tree.widgets[node.id] for node in model.nodes.values()}
        tree.root.show()
        QTest.qWait(100)
        assert controls["table"].verticalHeader().isHidden()
        assert controls["model_table"].horizontalHeader().isHidden()
        controls["table"].sortByColumn(0, Qt.SortOrder.AscendingOrder)
        assert controls["table"].item(0, 1).text() == "表格组件"
        assert controls["mask"].text() == "123-456"
        assert controls["form_input"].y() > controls["form_label"].y()
        assert tree.root.grab().save(str(output / "preview.png"))
        result["native_preview"] = "passed"
    finally:
        tree.dispose()
    entry = export_project(model, registry, output / "export")
    probe = '''import runpy, sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
app = QApplication([])
window = runpy.run_path(sys.argv[1])["create_window"](app)
window.show()
app.processEvents()
controls = window.controls
assert controls["table"].verticalHeader().isHidden()
assert controls["model_table"].horizontalHeader().isHidden()
assert controls["list"].gridSize() == QSize(112, 56)
assert controls["mask"].text() == "123-456"
assert controls["sequence"].maximumSequenceLength() == 2
assert controls["form_input"].y() > controls["form_label"].y()
assert not any(name in sys.modules for name in ("core", "runtime", "widgets", "app"))
window.close()
print("passed")
'''
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="properties_check_") as temporary:
        completed = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", probe, str(entry)],
                                  cwd=temporary, env=environment, capture_output=True, text=True, timeout=30)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        result["isolated_export"] = "passed"
        settings = QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat)
        window = MainWindow(registry, settings=settings, enable_recovery=False, persist_settings=False)
        try:
            window.resize(1540, 990)
            window.show()
            document = window.open_path(path)
            selected = next(node.id for node in model.nodes.values() if node.code_name == "model_table")
            document.select(selected)
            window.page.canvas.fit_to_window()
            QTest.qWait(100)
            assert "show_horizontal_header" in window.properties.editors
            assert "header_alignment" in window.properties.editors
            window.properties.search.setText("表头")
            window.properties.tree.setColumnWidth(0, 162)
            QTest.qWait(50)
            assert window.grab().save(str(output / "designer.png"))
            editor = window.properties.editors["show_horizontal_header"]
            editor.click()
            QTest.qWait(50)
            assert document.model.nodes[selected].properties["show_horizontal_header"]
            assert not window.page.canvas.renderer.tree.widgets[selected].horizontalHeader().isHidden()
            document.undo()
            QTest.qWait(50)
            assert not document.model.nodes[selected].properties["show_horizontal_header"]
            assert window.page.canvas.renderer.tree.widgets[selected].horizontalHeader().isHidden()
            result["designer_properties"] = "passed"
            result["designer_edit_and_undo"] = "passed"
        finally:
            window.discard_all_for_test()
            window.close()
    atomic_write(output / "verification.json", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
