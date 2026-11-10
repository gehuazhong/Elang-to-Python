"""Default-value reuse must preserve immutable snapshots and registry identity."""

from dataclasses import FrozenInstanceError, replace

import pytest

from core.errors import DesignerError
from core.metadata import PropertySpec, WidgetSpec
from core.models import FrozenMap, freeze, thaw
from core.registry import WidgetRegistry


def test_replacing_property_defaults_does_not_change_other_specs(registry):
    original = registry.require("builtin.button")
    baseline = original.defaults()
    changed = replace(original, properties=tuple(replace(prop, default="Replacement") if prop.key == "text"
                                                else prop for prop in original.properties))
    assert changed.defaults()["text"] == "Replacement"
    assert original.defaults() == baseline
    assert changed.defaults().changed(text="Instance")["text"] == "Instance"
    assert changed.defaults()["text"] == "Replacement"
    with pytest.raises(FrozenInstanceError):
        original._defaults = FrozenMap()


def test_mutating_constructor_collections_cannot_change_defaults():
    source = [{"text": "Root", "children": [{"text": "Child", "children": []}]}]
    properties = [PropertySpec("tree_data", "Tree", "Content", "tree", source)]
    spec = WidgetSpec("test.tree", "Tree", "Test", "QTreeWidget", 1, "children", (120, 80), "tree", properties)
    expected = thaw(spec.defaults())
    source[0]["text"] = "Changed"
    properties.clear()
    assert thaw(spec.defaults()) == expected
    assert len(spec.properties) == 1
    with pytest.raises(TypeError):
        spec.defaults()["tree_data"][0]["text"] = "Changed"


def test_cached_defaults_do_not_enter_registry_fingerprint(registry):
    copied = WidgetRegistry()
    for spec in registry.specs.values():
        spec.defaults()
        copied.register(replace(spec))
    copied.freeze()
    assert copied.fingerprint == registry.fingerprint


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan"), object(), {1: "invalid key"}])
def test_fast_scalar_path_still_rejects_non_json_values(value):
    with pytest.raises(DesignerError):
        freeze({"nested": [value]})
