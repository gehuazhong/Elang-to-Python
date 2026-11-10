"""逐项核对注册属性在原生 Qt 对象上的实际值，覆盖增量修改与回退。"""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.metadata import PropertySpec
from core.models import ProjectModel
from core.registry import WidgetRegistry
from runtime.builder import RuntimeTree
from runtime.widget_properties import ENUMS
from widgets.builtin import create_registry


def samples(prop: PropertySpec) -> tuple[Any, ...]:
    if prop.value_type == "enum":
        return tuple(value for value, _ in prop.options)
    if prop.value_type == "bool":
        return (not prop.default, prop.default)
    if prop.value_type == "int":
        return (min(prop.maximum, max(prop.minimum, prop.default + 1)), prop.default)
    if prop.value_type == "float":
        return (2.0, prop.default)
    if prop.value_type in {"string", "multiline"}:
        return ("属性核对：中文和标点 ' \\ <文字>", prop.default)
    return ()


KINDS = tuple(key for key, spec in create_registry().specs.items() if spec.toolbox) + ("builtin.main_window",)


@pytest.mark.parametrize("kind", KINDS)
def test_native_property_matrix(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication, kind: str) -> None:
    if kind == "builtin.main_window":
        key = project.root_id
    else:
        project, key = create_node(project, registry, kind, 24, 24)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "属性矩阵基准"))
        spec = registry.require(kind)
        for prop in spec.properties:
            if not prop.qt_name or prop.key == "visible":
                continue
            for sample in samples(prop):
                candidate = set_property(project, registry, key, prop.key, sample)
                registry.validate(candidate)
                tree.apply(compile_plan(candidate, registry, "属性矩阵修改"))
                widget = tree.widgets[key]
                meta = widget.metaObject()
                actual = meta.property(meta.indexOfProperty(prop.qt_name)).read(widget)
                expected = ENUMS.get(prop.key, {}).get(sample, sample)
                assert actual == expected, (kind, prop.key, sample, actual)
                tree.apply(compile_plan(project, registry, "属性矩阵回退"))
    finally:
        tree.dispose()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
