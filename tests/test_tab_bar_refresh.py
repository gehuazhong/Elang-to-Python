"""Appearance updates must preserve native tab data, order and selection."""

import pytest
from PySide6.QtTest import QSignalSpy

from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.models import thaw
from runtime.advanced_views import TabBar
from runtime.builder import RuntimeTree


@pytest.mark.parametrize("inherited", [False, True])
def test_style_refresh_keeps_tab_selection_and_business_data(project, registry, qt_app, inherited):
    model, key = create_node(project, registry, "builtin.tab_bar", 20, 20)
    model = set_property(model, registry, key, "items", ["first", "second", "third"])
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "initial"))
        tabs = tree.widgets[key]
        tabs.setTabData(2, {"record": 42})
        tabs.setCurrentIndex(2)
        tabs.moveTab(2, 0)
        changes = QSignalSpy(tabs.currentChanged)
        changed = set_property(model, registry, model.root_id if inherited else key,
                               "foreground_color", "#246b92")
        tree.apply(compile_plan(changed, registry, "style"))
        assert tabs.tabText(tabs.currentIndex()) == "third"
        assert tabs.tabData(tabs.currentIndex()) == {"record": 42}
        assert [tabs.tabText(index) for index in range(3)] == ["third", "first", "second"]
        assert changes.count() == 0
        assert tree.widgets[key] is tabs
    finally:
        tree.dispose()


def test_explicit_tab_selection_keeps_metadata_and_user_signals(registry, qt_app):
    tabs = TabBar()
    values = thaw(registry.require("builtin.tab_bar").defaults())
    values.update(items=["first", "second", "third"], current_index=0)
    try:
        tabs.configure(values)
        tabs.setTabData(1, "business value")
        changes = QSignalSpy(tabs.currentChanged)
        tabs.configure({**values, "current_index": 1})
        assert tabs.currentIndex() == 1 and tabs.tabData(1) == "business value"
        assert changes.count() == 0
        tabs.setCurrentIndex(2)
        assert changes.count() == 1 and changes.at(0) == [2]
        tabs.configure({**values, "items": ["replacement"], "current_index": 0})
        assert tabs.count() == 1 and tabs.tabText(0) == "replacement"
        assert tabs.tabData(0) is None and tabs.currentIndex() == 0
        assert changes.count() == 1
    finally:
        tabs.deleteLater()


def test_configure_preserves_existing_signal_block(registry, qt_app):
    tabs = TabBar()
    try:
        tabs.blockSignals(True)
        tabs.configure(thaw(registry.require("builtin.tab_bar").defaults()))
        assert tabs.signalsBlocked()
    finally:
        tabs.deleteLater()
