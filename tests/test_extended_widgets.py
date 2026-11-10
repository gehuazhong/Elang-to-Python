"""扩展输入控件、规范值、事件映射与完整支持目录的验证。"""

from __future__ import annotations

import inspect
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import QDate, QPoint, QPointF, Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QTableView

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.clipboard import copy_fragment, decode_fragment, encode_fragment, paste_fragment
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import ProjectModel
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from designer.canvas import DesignerCanvas
from panels.properties import PropertyPanel
from panels.support_dialog import SupportDialog
from panels.temporal_editor import TemporalEditor
from runtime.builder import FACTORIES, RuntimeTree, verify_registry
from runtime.preview import PreviewRuntime
from runtime.widget_properties import ENUMS
from tests.test_codegen import load_export
from widgets.catalog import COMPONENT_CLASSES
from widgets.support import WIDGET_INVENTORY, support_rows

VALUES: dict[str, dict[str, Any]] = {
    "group_box": {"text": "参数设置", "content_left": 18, "content_top": 40, "font_size": 14},
    "frame": {"line_width": 3, "frame_shadow": "sunken", "content_top": 20},
    "double_spin_box": {"decimals": 3, "minimum": -100.125, "maximum": 200.375, "value": 12.345, "single_step": 0.125, "suffix": " 米"},
    "date_edit": {"minimum": "2024-02-28", "maximum": "2024-03-01", "value": "2024-02-29"},
    "time_edit": {"minimum": "08:00:00", "maximum": "18:59:59", "value": "09:18:37"},
    "datetime_edit": {"minimum": "2024-03-09T00:00:00", "maximum": "2024-03-11T23:59:59", "value": "2024-03-10T02:30:00"},
    "calendar": {"minimum": "2024-02-01", "maximum": "2024-03-31", "value": "2024-02-29", "first_day": "sunday", "grid_visible": True},
    "tool_button": {"text": "运行", "arrow_type": "right", "tool_style": "beside", "checked": True},
    "command_link_button": {"text": "创建项目", "description": "开始创建新的界面", "checked": True},
    "dial": {"value": 42, "wrapping": True},
    "scroll_bar": {"value": 72, "orientation": "vertical", "inverted": True},
    "lcd_number": {"value": -123456, "digit_count": 10, "segment_style": "filled"},
}


def configure(model: ProjectModel, registry: WidgetRegistry, kind: str) -> tuple[ProjectModel, str]:
    model, key = create_node(model, registry, "builtin." + kind, 32, 40)
    for field, value in VALUES[kind].items():
        model = set_property(model, registry, key, field, value)
    registry.validate(model)
    return model, key


def state(widget: Any, kind: str) -> Any:
    if kind == "date_edit":
        return widget.date().toString("yyyy-MM-dd"), widget.minimumDate().toString("yyyy-MM-dd"), widget.maximumDate().toString("yyyy-MM-dd")
    if kind == "time_edit":
        return widget.time().toString("HH:mm:ss"), widget.minimumTime().toString("HH:mm:ss"), widget.maximumTime().toString("HH:mm:ss")
    if kind == "datetime_edit":
        return widget.dateTime().toString("yyyy-MM-ddTHH:mm:ss"), widget.minimumDateTime().toString("yyyy-MM-ddTHH:mm:ss"), widget.dateTime().offsetFromUtc()
    if kind == "calendar":
        return widget.selectedDate().toString("yyyy-MM-dd"), widget.yearShown(), widget.monthShown()
    if kind in {"dial", "scroll_bar", "double_spin_box"}:
        return widget.minimum(), widget.maximum(), widget.value(), widget.singleStep()
    if kind in {"group_box", "frame"}:
        return widget.contentsRect().getRect()
    return widget.intValue() if kind == "lcd_number" else widget.text()


@pytest.mark.parametrize("kind", VALUES)
def test_extended_roundtrip_copy_preview_export(project: ProjectModel, registry: WidgetRegistry,
                                               qt_app: QApplication, tmp_path: Path, kind: str) -> None:
    verify_registry(registry)
    project, key = configure(project, registry, kind)
    fragment = decode_fragment(encode_fragment(copy_fragment(project, registry, key)), registry)
    copied, copy_key = paste_fragment(project, registry, fragment)
    assert copied.nodes[copy_key].properties == project.nodes[key].properties
    path = tmp_path / "扩展组件.uipro"
    commit_project(path, project, expected_token=None)
    loaded = load_project(path).model
    assert loaded == project
    tree, preview = RuntimeTree(registry), PreviewRuntime(registry)
    generated = load_export(export_project(loaded, registry, tmp_path / "导出"), qt_app)
    try:
        plan = compile_plan(project, registry, "扩展组件验证")
        tree.apply(plan)
        preview.show(plan, project)
        expected = tree.widgets[key]
        for actual in (generated.controls[project.nodes[key].code_name], preview.tree.widgets[key]):
            assert actual.geometry() == expected.geometry()
            assert state(actual, kind) == state(expected, kind)
            for prop in registry.require("builtin." + kind).properties:
                if prop.qt_name and prop.key != "visible":
                    assert actual.property(prop.qt_name) == expected.property(prop.qt_name), prop.key
        if kind in {"date_edit", "time_edit", "datetime_edit", "calendar"}:
            assert state(expected, kind)[0] == VALUES[kind]["value"]
        if kind in {"dial", "scroll_bar", "double_spin_box"}:
            assert expected.value() == VALUES[kind]["value"]
        assert not tree.image(key, 1).isNull()
    finally:
        preview.dispose()
        tree.dispose()
        generated.close()
        generated.deleteLater()


@pytest.mark.parametrize("kind", VALUES)
def test_extended_enum_roundtrip_and_chinese_editors(project: ProjectModel, registry: WidgetRegistry,
                                                    qt_app: QApplication, kind: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 32, 40)
    document = DocumentSession(project, registry)
    document.select(key)
    canvas, panel = DesignerCanvas(document), PropertyPanel()
    panel.bind(document)
    try:
        for prop in registry.require("builtin." + kind).properties:
            if prop.value_type in {"date", "time", "datetime"}:
                assert isinstance(panel.editors[prop.key], TemporalEditor)
            if prop.value_type == "float":
                assert isinstance(panel.editors[prop.key], QDoubleSpinBox)
            if prop.value_type == "enum":
                for option, _ in prop.options:
                    document.execute("切换枚举", lambda model: set_property(model, registry, key, prop.key, option))
                    if prop.qt_name and prop.key in ENUMS:
                        assert canvas.renderer.tree.widgets[key].property(prop.qt_name) == ENUMS[prop.key][option]
        assert all("event." + event.key in panel.editors for event in registry.require("builtin." + kind).events)
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()
        canvas.dispose()
        canvas.close()


def test_decimal_rounding_and_reversible_range(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    project, key = configure(project, registry, "double_spin_box")
    document = DocumentSession(project, registry)
    tree = RuntimeTree(registry)
    try:
        document.execute("降低精度", lambda model: set_property(model, registry, key, "decimals", 2))
        values = document.model.nodes[key].properties
        assert (values["minimum"], values["maximum"], values["value"], values["single_step"]) == (-100.13, 200.38, 12.35, 0.13)
        tree.apply(compile_plan(document.model, registry, "小数精度"))
        assert tree.widgets[key].value() == 12.35
        document.undo()
        tree.apply(compile_plan(document.model, registry, "撤销小数精度"))
        assert tree.widgets[key].value() == 12.345
        document.execute("缩小范围", lambda model: set_property(model, registry, key, "maximum", 10.125))
        assert document.model.nodes[key].properties["value"] == 10.125
        document.undo()
        assert document.model == project
        for prop, value in (("value", float("nan")), ("value", float("inf")), ("value", True),
                            ("value", 10 ** 1000), ("value", 1.2345), ("single_step", 0.0)):
            before = document.model
            with pytest.raises(DesignerError):
                document.execute("无效小数", lambda model: set_property(model, registry, key, prop, value))
            assert document.model is before
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind,invalid", [("date_edit", "2023-02-29"), ("date_edit", "1700-01-01"),
    ("date_edit", "2024-2-29"), ("time_edit", "24:00:00"), ("time_edit", "12:60:00"),
    ("datetime_edit", "2024-03-10T02:30:00+08:00"), ("calendar", "2024-04-31")])
def test_invalid_temporal_does_not_change_history(project: ProjectModel, registry: WidgetRegistry, kind: str, invalid: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 32, 40)
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError):
        document.execute("无效日期时间", lambda model: set_property(model, registry, key, "value", invalid))
    assert document.model is project and document.history.cursor == 0


@pytest.mark.parametrize("kind,new_max", [("date_edit", "2024-02-28"), ("time_edit", "08:30:00"),
                                          ("datetime_edit", "2024-03-10T01:00:00"), ("calendar", "2024-02-20")])
def test_temporal_clamp_and_undo(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication, kind: str, new_max: str) -> None:
    project, key = configure(project, registry, kind)
    document = DocumentSession(project, registry)
    tree = RuntimeTree(registry)
    try:
        document.execute("调整日期范围", lambda model: set_property(model, registry, key, "maximum", new_max))
        tree.apply(compile_plan(document.model, registry, "日期范围"))
        assert state(tree.widgets[key], kind)[0] == new_max
        document.undo()
        tree.apply(compile_plan(document.model, registry, "日期撤销"))
        assert state(tree.widgets[key], kind)[0] == VALUES[kind]["value"]
    finally:
        tree.dispose()


def test_inventory_matches_installed_widgets_and_registered_factories(registry: WidgetRegistry, qt_app: QApplication) -> None:
    names = {name for name, cls in inspect.getmembers(QtWidgets, inspect.isclass)
             if name.startswith("Q") and issubclass(cls, QtWidgets.QWidget)}
    assert names == {name for name, _, _ in WIDGET_INVENTORY}
    assert COMPONENT_CLASSES == set(FACTORIES) == {spec.qt_class for spec in registry.specs.values()}
    rows = support_rows(registry)
    assert sum(row.status == "已接入" for row in rows) == sum(spec.toolbox for spec in registry.specs.values()) == 72
    assert next(row for row in rows if row.label == "图片框").status == "已接入"
    verify_registry(registry)


def test_support_dialog_searches_missing_components_and_chinese_properties(registry: WidgetRegistry, qt_app: QApplication) -> None:
    dialog = SupportDialog(registry)
    try:
        dialog.search.setText("菜单栏")
        visible = [dialog.tree.topLevelItem(i) for i in range(dialog.tree.topLevelItemCount()) if not dialog.tree.topLevelItem(i).isHidden()]
        assert len(visible) == 1 and visible[0].text(1) == "窗口结构"
        dialog.search.setText("小数位数")
        visible = [dialog.tree.topLevelItem(i) for i in range(dialog.tree.topLevelItemCount()) if not dialog.tree.topLevelItem(i).isHidden()]
        assert any(item.text(0) == "小数输入框" and item.isExpanded() for item in visible)
    finally:
        dialog.deleteLater()


def test_extended_export_runs_without_designer(project: ProjectModel, registry: WidgetRegistry, tmp_path: Path) -> None:
    for kind in VALUES:
        project, _ = configure(project, registry, kind)
    entry = export_project(project, registry, tmp_path / "独立扩展")
    code = '''import importlib.util, sys
from PySide6.QtWidgets import QApplication
application = QApplication([])
spec = importlib.util.spec_from_file_location("入口", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
window = module.create_window(application)
assert window.controls['date_edit_1'].date().toString('yyyy-MM-dd') == '2024-02-29'
assert window.controls['datetime_edit_1'].dateTime().toString('yyyy-MM-ddTHH:mm:ss') == '2024-03-10T02:30:00'
assert window.controls['double_spin_box_1'].value() == 12.345
assert len(window.controls) == 14
assert not any(name in sys.modules for name in ('core','runtime','widgets','app'))
window.close()
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(entry)], cwd=tmp_path,
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind", ["date_edit", "datetime_edit"])
def test_date_popup_survives_refresh_and_commits_with_undo(project: ProjectModel, registry: WidgetRegistry,
                                                        qt_app: QApplication, kind: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 32, 40)
    document = DocumentSession(project, registry)
    document.select(key)
    panel = PropertyPanel()
    panel.bind(document)
    panel.resize(480, 760)
    panel.show()
    try:
        panel.search.setText("当前日期")
        QTest.qWait(20)
        editor = panel.editors["value"]
        editor.setFocus()
        QTest.mouseClick(editor, Qt.MouseButton.LeftButton, pos=QPoint(editor.width() - 9, editor.height() // 2))
        QTest.qWait(20)
        assert editor.choosing
        panel.queue_refresh()
        QTest.qWait(20)
        assert panel.editors["value"] is editor and editor.choosing
        calendar = editor.calendarWidget()
        calendar.setSelectedDate(QDate(2024, 2, 29))
        dates = calendar.findChild(QTableView, "qt_calendar_calendarview")
        assert dates is not None
        QTest.mouseClick(dates.viewport(), Qt.MouseButton.LeftButton, pos=dates.visualRect(dates.currentIndex()).center())
        panel.search.setFocus()
        QTest.qWait(20)
        assert document.model.nodes[key].properties["value"].startswith("2024-02-29")
        document.undo()
        assert document.model == project
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()
