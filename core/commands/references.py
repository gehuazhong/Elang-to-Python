"""Maintain code-name references when copying controls between documents."""

from dataclasses import replace
from collections.abc import Mapping, Set

from core.models import WidgetNode


REFERENCE_KEYS = ("trigger_control", "navigation_page")


def omit_external_references(node: WidgetNode, included: Set[str]) -> tuple[WidgetNode, int]:
    changes = {key: "" for key in REFERENCE_KEYS if node.properties.get(key)
               and node.properties[key] not in included}
    omitted = len(changes)
    if node.type_id == "builtin.button_group" and "members" in node.properties:
        members = tuple(name for name in node.properties["members"] if name in included)
        removed = len(node.properties["members"]) - len(members)
        if removed:
            changes["members"] = members
            omitted += removed
    return (replace(node, properties=node.properties.changed(**changes)) if changes else node), omitted


def remap_references(node: WidgetNode, names: Mapping[str, str]) -> WidgetNode:
    changes = {key: names.get(node.properties[key], "") for key in REFERENCE_KEYS if key in node.properties}
    if node.type_id == "builtin.button_group" and "members" in node.properties:
        changes["members"] = tuple(names[name] for name in node.properties["members"] if name in names)
    return replace(node, properties=node.properties.changed(**changes)) if changes else node
