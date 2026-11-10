"""在接入界面前验证生产模型、历史、保存身份和构建计划。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from core.build_plan import compile_plan
from core.commands.nodes import create_node, delete_node, move_node, set_property
from core.document import ChangeSet, DocumentSession
from core.errors import DesignerError
from core.migrations import migrate
from core.models import FrozenMap, ProjectModel, new_project
from core.registry import WidgetRegistry
from core.validation import validate_project


def with_button(project: ProjectModel, registry: WidgetRegistry) -> tuple[ProjectModel, str]:
    return create_node(project, registry, "builtin.button", 24, 40)


def test_json_roundtrip_preserves_extensions_and_is_immutable(project: ProjectModel) -> None:
    raw = project.to_dict()
    raw["未来字段"] = {"数据": ["中文", 1]}
    raw["nodes"][0]["插件附加数据"] = {"数组": [1, 2]}
    frozen = ProjectModel.from_dict(raw)
    assert frozen.to_dict() == raw
    raw["未来字段"]["数据"].append("外部修改")
    assert frozen.data["未来字段"]["数据"] == ("中文", 1)
    with pytest.raises(TypeError):
        frozen.nodes["外部节点"] = None
    with pytest.raises(TypeError):
        frozen.data["name"] = "直接修改"


def test_migration_preserves_identity_and_repeats(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, _ = with_button(project, registry)
    old = project.to_dict()
    old["schema_version"] = 1
    for node in old["nodes"]:
        node["order"] = node.pop("object_order")
        node.pop("stack_order")
    new = migrate(old)
    assert old["schema_version"] == 1 and "order" in old["nodes"][0]
    assert migrate(new) == new
    validate_project(ProjectModel.from_dict(new))
    assert new["document_id"] == old["document_id"]


@pytest.mark.parametrize("value", [True, 0, 3, 900])
def test_unsupported_schema_is_rejected(project: ProjectModel, value: Any) -> None:
    raw = project.to_dict()
    raw["schema_version"] = value
    with pytest.raises(DesignerError):
        migrate(raw)


def test_stack_order_is_independent(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, first = with_button(project, registry)
    project, second = with_button(project, registry)
    updated = project.with_nodes({first: replace(project.nodes[first], stack_order=1),
                                 second: replace(project.nodes[second], stack_order=0)})
    validate_project(updated)
    assert updated.nodes[first].object_order == 0
    assert updated.nodes[second].object_order == 1
    with pytest.raises(DesignerError, match="唯一且连续"):
        validate_project(updated.with_nodes({second: replace(updated.nodes[second], stack_order=1)}))


def test_failed_edit_preserves_redo_and_saved_identity(project: ProjectModel, registry: WidgetRegistry,
                                                       qt_app: QApplication) -> None:
    document = DocumentSession(project, registry, saved=True)
    document.execute("改标题", lambda model: set_property(model, registry, model.root_id, "window_title", "新标题"))
    document.undo()
    before, revision = document.model, document.revision
    with pytest.raises(DesignerError):
        document.execute("无效名称", lambda model: set_property(model, registry, model.root_id, "name", ""))
    assert document.model is before and document.revision == revision
    assert document.history.can_redo and not document.dirty
    document.redo()
    assert document.dirty


@pytest.mark.parametrize("operation", ["edit", "undo", "redo", "begin_save", "finish_save"])
def test_preparation_cannot_reenter(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication,
                                   tmp_path: Path, operation: str) -> None:
    document = DocumentSession(project, registry)
    document.execute("标题甲", lambda model: set_property(model, registry, model.root_id, "window_title", "甲"))
    ticket = document.begin_save(tmp_path / "项目.uipro", None)
    document.execute("标题乙", lambda model: set_property(model, registry, model.root_id, "window_title", "乙"))
    document.undo()
    before, state, revision = document.model, document.state_id, document.revision

    def invalid(model: ProjectModel) -> ProjectModel:
        if operation == "edit":
            document.execute("重入", lambda nested: nested)
        elif operation == "undo":
            document.undo()
        elif operation == "redo":
            document.redo()
        elif operation == "begin_save":
            document.begin_save(tmp_path / "项目.uipro", None)
        else:
            document.finish_save(ticket, success=True, token="无效回执")
        return model

    with pytest.raises(DesignerError, match="准备或通知期间"):
        document.execute("不应成功", invalid)
    assert document.model is before and document.state_id == state and document.revision == revision
    assert document.history.can_redo
    document.finish_save(ticket, success=True, token="实际回执")
    assert not document.dirty


def test_listener_failure_is_isolated(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    document = DocumentSession(project, registry)
    observed: list[int] = []

    def reenter(change: ChangeSet) -> None:
        document.execute("重入修改", lambda model: model)

    document.subscribe(reenter)
    document.subscribe(lambda change: observed.append(change.revision))
    document.execute("改标题", lambda model: set_property(model, registry, model.root_id, "window_title", "有效标题"))
    assert observed == [1] and document.revision == 1
    assert document.model.nodes[project.root_id].properties["window_title"] == "有效标题"


def test_save_receipt_for_old_snapshot_keeps_new_edit_dirty(project: ProjectModel, registry: WidgetRegistry,
                                                           qt_app: QApplication, tmp_path: Path) -> None:
    document = DocumentSession(project, registry)
    ticket = document.begin_save(tmp_path / "项目.uipro", None)
    document.execute("改标题", lambda model: set_property(model, registry, model.root_id, "window_title", "后续编辑"))
    document.finish_save(ticket, success=True, token="落盘摘要")
    assert document.dirty
    document.undo()
    assert not document.dirty
    with pytest.raises(DesignerError, match="不属于"):
        document.finish_save(ticket, success=True)


def test_history_shares_unchanged_nodes_and_trims_full_commands(project: ProjectModel, registry: WidgetRegistry,
                                                              qt_app: QApplication) -> None:
    project, button = with_button(project, registry)
    document = DocumentSession(project, registry, saved=True, budget_bytes=5000)
    root = project.nodes[project.root_id]
    for number in range(20):
        document.execute("移动", lambda model, position=number: move_node(model, button, position * 8, 40))
        assert document.model.nodes[project.root_id] is root
        assert document.history.retained_bytes <= 5000
    assert 0 < len(document.history.commands) < 20
    state = document.model.to_bytes()
    while document.history.can_undo:
        document.undo()
    while document.history.can_redo:
        document.redo()
    assert document.model.to_bytes() == state
    assert document.dirty


def test_oversized_edit_does_not_discard_history(project: ProjectModel, registry: WidgetRegistry,
                                               qt_app: QApplication) -> None:
    document = DocumentSession(project, registry, budget_bytes=3000)
    document.execute("标题", lambda model: set_property(model, registry, model.root_id, "window_title", "甲"))
    document.undo()
    before = document.model
    with pytest.raises(DesignerError, match="预算"):
        document.execute("大标题", lambda model: set_property(model, registry, model.root_id, "window_title", "文" * 10000))
    assert document.model is before and document.history.can_redo


def test_replay_250_edits_and_delete_is_exact(project: ProjectModel, registry: WidgetRegistry,
                                            qt_app: QApplication) -> None:
    project, button = with_button(project, registry)
    document = DocumentSession(project, registry, saved=True)
    initial = project.to_bytes()
    for number in range(250):
        document.execute("移动", lambda model, position=number: move_node(model, button, position + 1, position % 70))
    document.execute("删除", lambda model: delete_node(model, button))
    final = document.model.to_bytes()
    while document.history.can_undo:
        document.undo()
    assert document.model.to_bytes() == initial and not document.dirty
    while document.history.can_redo:
        document.redo()
    assert document.model.to_bytes() == final


def test_plan_is_stable_and_registry_is_frozen(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, button = with_button(project, registry)
    original = project.to_bytes()
    first = compile_plan(project, registry, "同一状态")
    second = compile_plan(project, registry, "同一状态")
    assert first == second and project.to_bytes() == original
    positions = {node.id: order for order, node in enumerate(first.nodes)}
    assert positions[project.root_id] < positions[project.central_id] < positions[button]
    with pytest.raises(DesignerError, match="不能修改"):
        registry.register(registry.require("builtin.button"))


def test_unknown_type_preserves_data_and_strict_build_rejects(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, button = with_button(project, registry)
    project = project.with_nodes({button: replace(project.nodes[button], type_id="plugin.future",
                                                 properties=FrozenMap({"中文扩展": [1, 2]}))})
    with pytest.raises(DesignerError, match="构建适配器"):
        compile_plan(project, registry, "状态")
    plan = compile_plan(project, registry, "状态", allow_unknown=True)
    assert next(node for node in plan.nodes if node.id == button).unknown
    assert plan.diagnostics
    assert ProjectModel.from_dict(project.to_dict()) == project
