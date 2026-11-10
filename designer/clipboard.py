"""系统剪贴板只传递版本化 JSON，不保存控件实例或可执行对象。"""

from __future__ import annotations

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication

from core.commands.clipboard import ComponentFragment, decode_fragment, encode_fragment
from core.commands.group_clipboard import GroupFragment, decode_group, encode_group
from core.commands.tree_clipboard import TreeFragment, decode_tree, encode_tree
from core.errors import require
from core.registry import WidgetRegistry

WIDGET_MIME = "application/x-uiplay-widget+json"
GROUP_MIME = "application/x-uiplay-widgets+json"
TREE_MIME = "application/x-uiplay-widget-tree+json"


def has_component() -> bool:
    mime = QApplication.clipboard().mimeData()
    return mime is not None and any(mime.hasFormat(kind) for kind in (WIDGET_MIME, GROUP_MIME, TREE_MIME))


def write_component(fragment: ComponentFragment | GroupFragment | TreeFragment) -> None:
    group = isinstance(fragment, GroupFragment)
    if isinstance(fragment, TreeFragment):
        data, mime_type = encode_tree(fragment), TREE_MIME
    else:
        data = encode_group(fragment) if group else encode_fragment(fragment)
        mime_type = GROUP_MIME if group else WIDGET_MIME
    mime = QMimeData()
    mime.setData(mime_type, data)
    mime.setText(f"界面控件：{len(fragment.nodes)} 个" if isinstance(fragment, (GroupFragment, TreeFragment)) else f"界面控件：{fragment.node.name}")
    QApplication.clipboard().setMimeData(mime)
    current = QApplication.clipboard().mimeData()
    require(current is not None and bytes(current.data(mime_type)) == data, "写入剪贴板失败，请重试。")


def read_component(registry: WidgetRegistry) -> ComponentFragment | GroupFragment | TreeFragment:
    mime = QApplication.clipboard().mimeData()
    if mime is not None and mime.hasFormat(TREE_MIME):
        return decode_tree(bytes(mime.data(TREE_MIME)), registry)
    if mime is not None and mime.hasFormat(GROUP_MIME):
        return decode_group(bytes(mime.data(GROUP_MIME)), registry)
    require(mime is not None and mime.hasFormat(WIDGET_MIME), "剪贴板中没有可粘贴的界面控件，请先复制控件。")
    return decode_fragment(bytes(mime.data(WIDGET_MIME)), registry)
