"""菜单快捷键使用单组组合键，独立于 Qt 校验并保存稳定文本。"""

from .errors import require
from dataclasses import replace


def normalize_shortcut(value):
    require(isinstance(value, str) and len(value) <= 80, "快捷键必须是有效组合键。")
    if not value.strip():
        return ""
    remaining = value.strip()
    modifiers = []
    while "+" in remaining and remaining != "+":
        prefix, rest = remaining.split("+", 1)
        modifier = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "meta": "Meta"}.get(prefix.casefold())
        if modifier is None:
            break
        require(modifier not in modifiers, "快捷键修饰键不能重复。")
        modifiers.append(modifier)
        remaining = rest
    names = {name.casefold(): name for name in (
        "Esc", "Tab", "Backtab", "Backspace", "Return", "Enter", "Ins", "Del", "Pause", "Print",
        "Home", "End", "Left", "Up", "Right", "Down", "PgUp", "PgDown", "Space", "Menu", "Help",
        "CapsLock", "NumLock", "ScrollLock", *(f"F{i}" for i in range(1, 36)))}
    key = names.get(remaining.casefold())
    if key is None and len(remaining) == 1 and remaining.isascii() and 33 <= ord(remaining) <= 126:
        key = remaining.upper()
    require(key is not None, "快捷键无效，请使用 Ctrl+O、F5 等单组组合键。")
    return "+".join([part for part in ("Meta", "Ctrl", "Alt", "Shift") if part in modifiers] + [key])


def _shortcuts(model, registry):
    for node in model.nodes.values():
        spec = registry.get(node.type_id)
        if spec is None or node.type_version != spec.version or not any(prop.key == "shortcut" for prop in spec.properties):
            continue
        shortcut = normalize_shortcut(node.properties.get("shortcut", ""))
        if shortcut:
            yield node, shortcut.casefold()


def normalize_key_sequence(value):
    require(isinstance(value, str) and len(value) <= 320, "快捷键序列必须是有效文本。")
    if not value.strip():
        return ""
    parts = value.strip().split(", ")
    require(1 <= len(parts) <= 4 and all(part.strip() for part in parts), "快捷键序列最多包含四组组合键。")
    return ", ".join(normalize_shortcut(part) for part in parts)


def validate_shortcuts(model, registry):
    shortcuts = {}
    for node, shortcut in _shortcuts(model, registry):
        require(shortcut not in shortcuts,
                f"快捷键重复：“{node.name}”与“{shortcuts.get(shortcut, '')}”使用同一组合键。")
        shortcuts[shortcut] = node.name


def resolve_pasted_shortcuts(model, registry, copied_ids):
    """粘贴保留目标窗口已有绑定，仅清除新副本中发生冲突的执行快捷键。"""
    copied = set(copied_ids)
    sequences = {node.id: shortcut for node, shortcut in _shortcuts(model, registry)}
    used = {shortcut for key, shortcut in sequences.items() if key not in copied}
    changes = {}
    for key in copied_ids:
        shortcut = sequences.get(key)
        if not shortcut:
            continue
        if shortcut in used:
            node = model.nodes[key]
            changes[key] = replace(node, properties=node.properties.changed(shortcut=""))
        else:
            used.add(shortcut)
    return model.with_nodes(changes) if changes else model
