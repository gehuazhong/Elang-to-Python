"""预览和独立导出共用的事件连接；仅订阅所选项并独立管理生命周期。"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
import sys
from typing import Any, Callable
from uuid import uuid4

from PySide6.QtCore import QEvent, QMetaMethod, QObject, Qt
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QAbstractSpinBox, QCalendarWidget,
                              QComboBox, QKeySequenceEdit, QLineEdit, QTabBar, QToolBar, QToolButton, QWidget)
from shiboken6 import isValid

logger = logging.getLogger(__name__)
Handler = Callable[[dict[str, Any], tuple[Any, ...]], Any]
POINTER_EVENTS = {"MouseButtonPress", "MouseButtonRelease", "MouseButtonDblClick", "MouseMove",
                  "Enter", "Leave", "Wheel", "ContextMenu", "DragEnter", "DragMove", "DragLeave", "Drop"}
EDITOR_EVENTS = {"KeyPress", "KeyRelease", "InputMethod", "FocusIn", "FocusOut"}


class EventConnections(QObject):
    def __init__(self, owner: QObject, controls: dict[str, QObject], bindings: tuple | list,
                 handler: Handler, error: Callable[[str], None] | None = None) -> None:
        super().__init__(owner)
        self._controls = controls
        self._handler = handler
        self._error = error
        self._signals = []
        self._filters: dict[QObject, dict[QEvent.Type, list[dict]]] = {}
        self._settings: dict[tuple[QWidget, str], Any] = {}
        self._active: set[str] = set()
        self._disposed = False
        try:
            for binding in bindings:
                widget = controls[binding["control"]]
                if "slot" in binding and not callable(getattr(controls[binding["target"]], binding["slot"], None)):
                    raise ValueError(f"“{binding['name']}”的事件目标不支持所选操作。")
                if binding["signal"]:
                    signal = getattr(widget, binding["signal"], None)
                    if signal is None or not callable(getattr(signal, "connect", None)):
                        raise ValueError(f"“{binding['name']}”不支持“{binding['label']}”信号。")
                    # clicked(bool) 等含默认参数的信号还有无参数重载，明确选择完整签名。
                    meta = widget.metaObject()
                    signatures = [meta.method(i) for i in range(meta.methodCount())
                                  if meta.method(i).methodType() == QMetaMethod.MethodType.Signal
                                  and bytes(meta.method(i).name()).decode() == binding["signal"]]
                    if signatures:
                        method = max(signatures, key=lambda item: item.parameterCount())
                        signal = signal[tuple(bytes(item).decode() for item in method.parameterTypes())]
                    self._signals.append(signal.connect(lambda *args, item=binding: self._dispatch(item, args)))
                    if binding["signal"] == "customContextMenuRequested":
                        self._setting(widget, "contextMenuPolicy", Qt.ContextMenuPolicy.CustomContextMenu)
                    if binding["signal"] in {"entered", "itemEntered", "viewportEntered"}:
                        self._setting(widget, "mouseTracking", True)
                        if isinstance(widget, QAbstractScrollArea):
                            self._setting(widget.viewport(), "mouseTracking", True)
                else:
                    for watched in self._targets(widget, binding["event"]):
                        if watched not in self._filters:
                            self._filters[watched] = {}
                            watched.installEventFilter(self)
                        kind = getattr(QEvent.Type, binding["event"])
                        self._filters[watched].setdefault(kind, []).append(binding)
                        if binding["event"] == "MouseMove":
                            self._setting(watched, "mouseTracking", True)
                        if binding["event"] in {"DragEnter", "DragMove", "DragLeave", "Drop"}:
                            self._setting(watched, "acceptDrops", True)
        except Exception:
            self.dispose()
            raise

    @staticmethod
    def _targets(widget: QObject, kind: str) -> tuple[QObject, ...]:
        if isinstance(widget, QKeySequenceEdit) and kind in POINTER_EVENTS | EDITOR_EVENTS:
            editor = widget.findChild(QLineEdit)
            if editor is not None:
                # 快捷键输入框自己持有键盘焦点，内部编辑框只负责显示。
                return (widget,) if kind in EDITOR_EVENTS else (widget, editor, *editor.findChildren(QToolButton))
        if isinstance(widget, QAbstractScrollArea) and kind in POINTER_EVENTS | {"Paint", "InputMethod"}:
            return (widget.viewport(),)
        if isinstance(widget, (QAbstractSpinBox, QComboBox)) and kind in POINTER_EVENTS | EDITOR_EVENTS:
            editor = widget.lineEdit()
            if editor is not None:
                # 键盘由内部编辑框接收；外框仍保留箭头区域的鼠标事件。
                return (editor,) if kind in EDITOR_EVENTS else (widget, editor)
        tab_bar = getattr(widget, "tab_bar", None)
        if isinstance(tab_bar, QTabBar) and kind in POINTER_EVENTS | EDITOR_EVENTS:
            return (tab_bar,)
        if isinstance(widget, QCalendarWidget):
            view = widget.findChild(QAbstractItemView)
            if view is not None and kind in POINTER_EVENTS | EDITOR_EVENTS:
                return (view.viewport(),) if kind in POINTER_EVENTS else (view,)
        if isinstance(widget, (QToolBar, QLineEdit)) and kind in POINTER_EVENTS - {"Enter", "Leave"}:
            return (widget, *widget.findChildren(QToolButton))
        return (widget,)

    def _setting(self, widget: QWidget, name: str, value: Any) -> None:
        key = (widget, name)
        if key not in self._settings:
            getter = "hasMouseTracking" if name == "mouseTracking" else name
            self._settings[key] = getattr(widget, getter)()
        getattr(widget, "set" + name[0].upper() + name[1:])(value)

    def _dispatch(self, binding: dict, arguments: tuple) -> Any:
        identity = binding["id"]
        if self._disposed or identity in self._active:
            return None
        self._active.add(identity)
        try:
            mapping = binding.get("arguments")
            values = arguments if mapping is None else tuple(
                arguments[item["index"]] if item["kind"] == "event_arg" else item.get("value") for item in mapping)
            if "slot" in binding:
                return getattr(self._controls[binding["target"]], binding["slot"])(*values)
            return self._handler(binding, values)
        except Exception:
            message = f"事件处理失败：{binding['name']} · {binding['label']}。请检查对应处理函数。"
            logger.exception(message)
            if self._error is not None:
                self._error(message)
            return None
        finally:
            self._active.discard(identity)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if self._disposed:
            return False
        consumed = False
        for binding in tuple(self._filters.get(watched, {}).get(event.type(), ())):
            consumed = (self._dispatch(binding, (event,)) is True) or consumed
            if not isValid(watched):
                return True
        return consumed

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        for connection in self._signals:
            if connection:
                QObject.disconnect(connection)
        self._signals.clear()
        for widget in self._filters:
            if isValid(widget):
                widget.removeEventFilter(self)
        self._filters.clear()
        for (widget, name), value in self._settings.items():
            if isValid(widget):
                getattr(widget, "set" + name[0].upper() + name[1:])(value)
        self._settings.clear()
        self._controls = {}
        self._handler = lambda item, args: None
        self._error = None


def connect_exported_events(window: QWidget, bindings: tuple | list, module_file: str) -> EventConnections:
    """业务文件在生成目录之外，每次运行读取当前内容，不缓存编译文件。"""
    base = Path(module_file).resolve().parents[2]
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    handlers = {}
    for binding in bindings:
        name = binding.get("handler")
        if name is None or name in handlers:
            continue
        path = base / "event_handlers" / (name + ".py")
        spec = importlib.util.spec_from_file_location("_uiplay_event_" + uuid4().hex, path)
        if spec is None:
            raise RuntimeError(f"无法加载事件处理函数：{name}。")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        window.destroyed.connect(lambda *args, module_name=spec.name: sys.modules.pop(module_name, None))
        function = getattr(module, name, None)
        if not callable(function):
            raise RuntimeError(f"事件文件缺少处理函数：{name}。")
        handlers[name] = function
    return EventConnections(window, window.controls, bindings,
                            lambda binding, args: handlers[binding["handler"]](window, *args))
