"""顺序分离、迁移及失败不改变文档的回归验证。"""

from __future__ import annotations

import random
from copy import deepcopy

import pytest

from architecture_checks.contracts import (
    ContractError, Project, ReferenceHistory, Snapshot,
    migrate_project, ordered_children, validate_project,
)


def children(project: Project) -> list[Project]:
    return [node for node in project["nodes"] if node["slot"] == "children"]


def horizontal(project: Project) -> str:
    parent = next(node for node in project["nodes"] if node["slot"] == "central")
    parent["layout"]["kind"] = "horizontal"
    for index, node in enumerate(children(project)):
        node["layout_item"] = {"index": index, "stretch": 0, "alignment": "inherit"}
    return parent["id"]


def test_stack_change_keeps_object_and_layout_order(project: Project) -> None:
    parent_id = horizontal(project)
    before_object = ordered_children(project, parent_id, "object")
    before_layout = ordered_children(project, parent_id, "layout")
    first, second = children(project)
    first["stack_order"], second["stack_order"] = second["stack_order"], first["stack_order"]
    validate_project(project)
    assert ordered_children(project, parent_id, "object") == before_object
    assert ordered_children(project, parent_id, "layout") == before_layout
    assert ordered_children(project, parent_id, "stack") == tuple(reversed(before_object))


@pytest.mark.parametrize("field", ["object_order", "stack_order"])
def test_duplicate_order_is_rejected(project: Project, field: str) -> None:
    children(project)[1][field] = children(project)[0][field]
    with pytest.raises(ContractError, match="唯一且连续"):
        validate_project(project)


def test_duplicate_layout_index_is_rejected(project: Project) -> None:
    horizontal(project)
    children(project)[1]["layout_item"]["index"] = 0
    with pytest.raises(ContractError, match="布局顺序"):
        validate_project(project)


def test_grid_overlap_is_rejected(project: Project) -> None:
    parent_id = horizontal(project)
    next(node for node in project["nodes"] if node["id"] == parent_id)["layout"]["kind"] = "grid"
    for node in children(project):
        node["layout_item"].update(row=0, column=0, row_span=1, column_span=1)
    with pytest.raises(ContractError, match="不能重叠"):
        validate_project(project)


def test_migration_is_pure_and_repeatable(project: Project) -> None:
    horizontal(project)
    old = deepcopy(project)
    old["schema_version"] = 1
    old["extensions"] = {"未知插件": {"原始值": [1, "中文"]}}
    for node in old["nodes"]:
        node["order"] = node.pop("object_order")
        node.pop("stack_order")
        if node["layout_item"] is not None:
            node["layout_item"].pop("index")
    original = deepcopy(old)
    migrated = migrate_project(old)
    assert old == original
    assert migrated["extensions"] == original["extensions"]
    assert migrate_project(migrated) == migrated
    for node in children(migrated):
        assert node["object_order"] == node["stack_order"] == node["layout_item"]["index"]


def test_future_version_is_rejected(project: Project) -> None:
    project["schema_version"] = 900
    with pytest.raises(ContractError, match="无法迁移"):
        migrate_project(project)


def test_failed_edit_preserves_state_and_redo(project: Project) -> None:
    history = ReferenceHistory(project)
    history.apply(lambda model: model.update(name="临时名称"))
    history.undo()
    before, revision = history.current, history.revision

    def invalid(model: Project) -> None:
        model["name"] = "不应提交"
        children(model)[0]["geometry"]["width"] = -1

    with pytest.raises(ContractError, match="尺寸必须为正"):
        history.apply(invalid)
    assert history.current is before
    assert history.revision == revision
    assert history.can_redo
    assert not history.dirty


def test_stale_edit_and_snapshot_alias_are_rejected(project: Project) -> None:
    history = ReferenceHistory(project)
    outside = history.current.project()
    outside["name"] = "外部修改"
    assert history.current.project()["name"] != "外部修改"
    history.apply(lambda model: model.update(name="已提交"))
    with pytest.raises(ContractError, match="已经过期"):
        history.apply(lambda model: model.update(name="旧操作"), expected_revision=0)


def test_listener_failure_and_reentry_do_not_corrupt_history(project: Project) -> None:
    history = ReferenceHistory(project)
    observed: list[str] = []

    def reenter(snapshot: Snapshot) -> None:
        history.apply(lambda model: model.update(name="重入修改"))

    history.subscribe(reenter)
    history.subscribe(lambda snapshot: observed.append(snapshot.project()["name"]))
    history.apply(lambda model: model.update(name="合法修改"))
    assert observed == ["合法修改"]
    assert history.current.project()["name"] == "合法修改"
    assert history.revision == 1
    history.undo()
    assert not history.dirty


@pytest.mark.parametrize("operation", ["apply", "undo", "redo", "begin_save", "finish_save"])
def test_preparation_reentry_preserves_history_and_save_ticket(project: Project, operation: str) -> None:
    history = ReferenceHistory(project)
    history.apply(lambda model: model.update(name="正在写盘的状态"))
    ticket = history.begin_save()
    history.apply(lambda model: model.update(name="可重做的状态"))
    history.undo()
    before, revision, dirty = history.current, history.revision, history.dirty

    def reenter(model: Project) -> None:
        model["name"] = "不能发布的候选状态"
        if operation == "apply":
            history.apply(lambda nested: nested.update(name="嵌套修改"))
        elif operation == "undo":
            history.undo()
        elif operation == "redo":
            history.redo()
        elif operation == "begin_save":
            history.begin_save()
        else:
            history.finish_save(ticket, success=True)

    with pytest.raises(ContractError, match="准备或通知期间"):
        history.apply(reenter)
    assert history.current is before
    assert history.revision == revision
    assert history.can_redo and history.dirty == dirty
    # 失败不能消耗原有保存票据，退出临界区后仍能正常保存和回放。
    history.finish_save(ticket, success=True)
    assert not history.dirty
    history.redo()
    assert history.current.project()["name"] == "可重做的状态"


def test_edit_during_save_remains_dirty_until_undo(project: Project) -> None:
    history = ReferenceHistory(project)
    history.apply(lambda model: model.update(name="正在保存的版本"))
    ticket = history.begin_save()
    history.apply(lambda model: model.update(name="保存期间的新编辑"))
    history.finish_save(ticket, success=True)
    assert history.dirty
    history.undo()
    assert not history.dirty
    history.redo()
    assert history.dirty


def test_save_failure_and_wrong_receipt_keep_saved_state(project: Project) -> None:
    history = ReferenceHistory(project)
    history.apply(lambda model: model.update(name="待保存"))
    ticket = history.begin_save()
    with pytest.raises(ContractError, match="只能有一个"):
        history.begin_save()
    stranger = ReferenceHistory(project).begin_save()
    with pytest.raises(ContractError, match="不属于"):
        history.finish_save(stranger, success=True)
    history.finish_save(ticket, success=False)
    assert history.dirty
    history.undo()
    assert not history.dirty


def test_random_edits_undo_and_redo_exactly(project: Project) -> None:
    history = ReferenceHistory(project)
    original = history.current.payload
    rng = random.Random(20261106)
    for index in range(250):
        value = rng.randrange(0, 800)

        def mutation(model: Project, number: int = index, coordinate: int = value) -> None:
            model["name"] = f"编辑序列{number}"
            children(model)[number % 2]["geometry"]["x"] = coordinate

        history.apply(mutation)
    result = history.current.payload
    for _ in range(250):
        history.undo()
    assert history.current.payload == original
    assert not history.dirty
    for _ in range(250):
        history.redo()
    assert history.current.payload == result


def test_new_branch_discards_redo_and_noop_changes_nothing(project: Project) -> None:
    history = ReferenceHistory(project)
    history.apply(lambda model: model.update(name="原分支"))
    history.undo()
    history.apply(lambda model: model.update(name="新分支"))
    state, revision = history.current, history.revision
    history.apply(lambda model: None)
    assert not history.can_redo
    assert history.current is state and history.revision == revision
