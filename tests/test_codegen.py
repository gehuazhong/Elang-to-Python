"""验证导出独立运行、原生属性一致性、业务保护与中断恢复。"""

from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
from uuid import uuid4

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow

from codegen.generator import generate_files
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.arrange import arrange_nodes
from core.commands.nodes import create_node, set_property
from core.errors import DesignerError
from core.models import ProjectModel, new_project
from core.registry import WidgetRegistry
from core.storage import FileLease
from runtime.application import configure_application
from runtime.builder import RuntimeTree


def load_export(entry: Path, application: QApplication) -> QMainWindow:
    spec = importlib.util.spec_from_file_location("_导出验收", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_window(application)


def complete_project(project: ProjectModel, registry: WidgetRegistry) -> ProjectModel:
    for index, type_id in enumerate(("builtin.button", "builtin.label", "builtin.line_edit")):
        project, key = create_node(project, registry, type_id, 48, 48 + 64 * index)
        values: dict[str, Any] = {"text": "中文 '引号' 与 \\ 路径", "font_size": 13,
                                  "background_color": "#fae7ce", "foreground_color": "#173444",
                                  "tool_tip": "中文提示", "enabled": True}
        if type_id == "builtin.button":
            values.update(checkable=True, checked=True)
        if type_id == "builtin.label":
            values.update(alignment="center", word_wrap=True)
        if type_id == "builtin.line_edit":
            values.update(max_length=100, echo_mode="password", read_only=True,
                          placeholder_text="请输入名称", alignment="right_vcenter", frame=False)
        for name, value in values.items():
            project = set_property(project, registry, key, name, value)
    return project


@pytest.mark.parametrize("border", ["standard", "fixed", "none"])
def test_native_properties_match_runtime(project: ProjectModel, registry: WidgetRegistry,
                                         qt_app: QApplication, tmp_path: Path, border: str) -> None:
    configure_application(qt_app)
    project = complete_project(project, registry)
    project = set_property(project, registry, project.root_id, "border_style", border)
    project = set_property(project, registry, project.root_id, "stay_on_top", True)
    entry = export_project(project, registry, tmp_path)
    assert generate_files(project, registry) == generate_files(project, registry)
    tree = RuntimeTree(registry, design_mode=False)
    tree.apply(compile_plan(project, registry, "导出差分"))
    generated = load_export(entry, qt_app)
    try:
        assert generated.windowFlags() == tree.root.windowFlags()
        assert generated.minimumSize() == tree.root.minimumSize()
        for key, expected in tree.widgets.items():
            actual = generated.controls[project.nodes[key].code_name]
            assert actual.geometry() == expected.geometry()
            assert actual.objectName() == expected.objectName()
            assert actual.font() == expected.font()
            assert actual.palette() == expected.palette()
            assert actual.isHidden() == expected.isHidden()
            for prop in registry.require(project.nodes[key].type_id).properties:
                if prop.qt_name:
                    assert actual.property(prop.qt_name) == expected.property(prop.qt_name), prop.key
    finally:
        tree.dispose()
        generated.close()
        generated.deleteLater()


@pytest.mark.parametrize("mode", ["same_width", "same_height", "same_size"])
def test_equal_size_geometry_matches_preview_and_export(project: ProjectModel, registry: WidgetRegistry,
                                                        qt_app: QApplication, tmp_path: Path, mode: str) -> None:
    project = complete_project(project, registry)
    keys = tuple(node.id for node in project.nodes.values() if node.slot == "children")
    project = arrange_nodes(project, keys, mode, keys[-1])
    tree = RuntimeTree(registry, design_mode=False)
    generated = None
    try:
        tree.apply(compile_plan(project, registry, "统一尺寸"))
        generated = load_export(export_project(project, registry, tmp_path), qt_app)
        for key in keys:
            node = project.nodes[key]
            rect = node.geometry
            expected = (rect.x, rect.y, rect.width, rect.height)
            assert tree.widgets[key].geometry().getRect() == expected
            assert generated.controls[node.code_name].geometry().getRect() == expected
    finally:
        tree.dispose()
        if generated is not None:
            generated.close()
            generated.deleteLater()


def test_independent_process_and_preserved_business(project: ProjectModel, registry: WidgetRegistry,
                                                    tmp_path: Path) -> None:
    project = complete_project(project, registry)
    entry = export_project(project, registry, tmp_path / "中文导出")
    handlers = entry.with_name("handlers.py")
    business = ('"""用户编写的业务。"""\n'
                'def connect_events(window) -> None:\n'
                '    window.controls["button_1"].clicked.connect(lambda: window.setWindowTitle("业务已执行"))\n')
    handlers.write_text(business, encoding="utf-8")
    old_pointer = entry.with_name("current.json").read_bytes()
    project = set_property(project, registry, project.root_id, "window_title", "再次导出")
    export_project(project, registry, entry.parent)
    assert handlers.read_text(encoding="utf-8") == business
    assert old_pointer != entry.with_name("current.json").read_bytes()
    code = '''import importlib.util, pathlib, sys
from PySide6.QtWidgets import QApplication
entry = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("导出入口", entry)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
application = QApplication([])
window = module.create_window(application)
assert window.windowTitle() == "再次导出"
window.controls["button_1"].click()
assert window.windowTitle() == "业务已执行"
assert not any(key == "core" or key == "app" or key == "runtime" for key in sys.modules)
window.close()
print("独立运行与业务绑定通过")
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(entry)],
                            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "业务绑定通过" in result.stdout


@pytest.mark.parametrize("stage", ["version.ready", "before.publish"])
@pytest.mark.parametrize("first", [True, False])
def test_interruption_and_retry(project: ProjectModel, registry: WidgetRegistry, tmp_path: Path,
                                qt_app: QApplication, stage: str, first: bool) -> None:
    if not first:
        export_project(project, registry, tmp_path)
    pointer = tmp_path / "current.json"
    before = pointer.read_bytes() if pointer.exists() else None
    project = set_property(project, registry, project.root_id, "window_title", "新版本")

    def fail(value: str) -> None:
        if value == stage:
            raise OSError("模拟磁盘中断")

    with pytest.raises(DesignerError):
        export_project(project, registry, tmp_path, checkpoint=fail)
    assert (pointer.read_bytes() if pointer.exists() else None) == before
    if not first:
        window = load_export(tmp_path / "main.py", qt_app)
        assert window.windowTitle() == "测试窗口"
        window.close()
        window.deleteLater()
    export_project(project, registry, tmp_path)
    assert json.loads(pointer.read_text(encoding="utf-8"))["document_id"] == project.data["document_id"]


@pytest.mark.parametrize("business", ["def 错误语法(\n", "def connect_events() -> None:\n    pass\n",
                                    "async def connect_events(window) -> None:\n    pass\n",
                                    "def other(window) -> None:\n    pass\n"])
def test_invalid_business_keeps_pointer(project: ProjectModel, registry: WidgetRegistry,
                                       tmp_path: Path, business: str) -> None:
    export_project(project, registry, tmp_path)
    pointer = (tmp_path / "current.json").read_bytes()
    (tmp_path / "handlers.py").write_text(business, encoding="utf-8")
    with pytest.raises(DesignerError, match="业务"):
        export_project(project, registry, tmp_path)
    assert (tmp_path / "current.json").read_bytes() == pointer
    assert (tmp_path / "handlers.py").read_text(encoding="utf-8") == business


def test_directory_ownership_and_lease(project: ProjectModel, registry: WidgetRegistry, tmp_path: Path) -> None:
    export_project(project, registry, tmp_path)
    with pytest.raises(DesignerError, match="其他项目"):
        export_project(new_project(), registry, tmp_path)
    lease = FileLease(tmp_path / "current.json")
    try:
        with pytest.raises(DesignerError, match="正在使用"):
            export_project(project, registry, tmp_path)
    finally:
        lease.release()


@pytest.mark.parametrize("name", ["not valid", "for", "_QMainWindow", "configure_application", "窗口", "dict", "RuntimeError"])
def test_invalid_class_does_not_touch_target(project: ProjectModel, registry: WidgetRegistry,
                                             tmp_path: Path, name: str) -> None:
    project = replace(project, data=project.data.changed(codegen=project.data["codegen"].changed(window_class=name)))
    with pytest.raises(DesignerError):
        export_project(project, registry, tmp_path / "目标")
    assert not (tmp_path / "目标").exists()


def test_unknown_property_and_literal_source(project: ProjectModel, registry: WidgetRegistry,
                                             tmp_path: Path, qt_app: QApplication) -> None:
    project, key = create_node(project, registry, "builtin.label", 16, 16)
    value = "引号'\"\n__import__('os').environ['不应执行']='错误'"
    project = set_property(project, registry, key, "text", value)
    window = load_export(export_project(project, registry, tmp_path), qt_app)
    assert window.controls["label_1"].text() == value
    window.close()
    window.deleteLater()
    node = project.nodes[key]
    project = project.with_nodes({key: replace(node, properties=node.properties.changed(unknown="不能遗漏"))})
    with pytest.raises(DesignerError, match="尚未支持"):
        generate_files(project, registry)


@pytest.mark.parametrize("feature", ["connections", "handlers", "resources", "extensions", "unknown"])
def test_unsupported_data_cannot_replace_export(project: ProjectModel, registry: WidgetRegistry,
                                               tmp_path: Path, feature: str) -> None:
    export_project(project, registry, tmp_path)
    before = (tmp_path / "current.json").read_bytes()
    values: dict[str, Any] = {
        "connections": [{"id": str(uuid4()), "source_id": project.root_id,
                         "target": {"kind": "slot", "node_id": project.root_id}}],
        "handlers": [{"id": str(uuid4()), "name": "处理函数"}],
        "resources": [{"id": str(uuid4()), "path": "assets/不存在.png", "sha256": "a" * 64}],
        "extensions": {"future": True}, "unknown": {"future": True},
    }
    changed = replace(project, data=project.data.changed(**{feature: values[feature]}))
    with pytest.raises(DesignerError):
        export_project(changed, registry, tmp_path)
    assert (tmp_path / "current.json").read_bytes() == before


def test_business_change_during_export_cannot_publish(project: ProjectModel, registry: WidgetRegistry,
                                                     tmp_path: Path) -> None:
    export_project(project, registry, tmp_path)
    before = (tmp_path / "current.json").read_bytes()
    project = set_property(project, registry, project.root_id, "window_title", "新标题")
    business = 'def connect_events(window) -> None:\n    window.setWindowTitle("用户修改")\n'

    def edit(stage: str) -> None:
        if stage == "before.publish":
            (tmp_path / "handlers.py").write_text(business, encoding="utf-8")

    with pytest.raises(DesignerError, match="发生了变化"):
        export_project(project, registry, tmp_path, checkpoint=edit)
    assert (tmp_path / "current.json").read_bytes() == before
    assert (tmp_path / "handlers.py").read_text(encoding="utf-8") == business
