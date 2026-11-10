"""把画布、对象树和菜单编辑路由到同一文档，隔离文本输入快捷键。"""

from __future__ import annotations

from layout.containers import PAGE_TYPES

from typing import TYPE_CHECKING, Callable

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QMenu, QPlainTextEdit, QTextEdit

from core.commands.clipboard import check_copyable, copy_fragment, paste_fragment
from core.commands.group_clipboard import GroupFragment, copy_group, paste_group
from core.commands.tree_clipboard import TreeFragment, copy_tree, paste_tree
from core.commands.hierarchy import reparent_node, require_container
from core.hierarchy import active_page, ancestors, content_origin, pages, selected_roots, subtree_ids
from core.commands.arrange import ARRANGEMENTS, STACKING, arrange_nodes, available_stacking, stack_nodes
from core.errors import DesignerError, require
from core.deferred import defer
from core.models import ProjectModel
from designer.clipboard import has_component, read_component, write_component

if TYPE_CHECKING:
    from app.main_window import MainWindow
    from designer.canvas import DesignerCanvas


class EditActions(QObject):
    def __init__(self, window: MainWindow, menu: QMenu) -> None:
        super().__init__(window)
        self.window = window
        self.menu: QMenu | None = None
        self._paste_identity: tuple[str, str] | None = None
        self._paste_count = 0
        self._disposed = False
        self._observed_editor: QLineEdit | QPlainTextEdit | QTextEdit | None = None
        for key in ("undo", "redo"):
            action = window.actions[key]
            # 文档历史仍可在非输入面板中调用；文本焦点由原生编辑器及动作状态隔离。
            window.object_tree.addAction(action)
        menu.addSeparator()
        for key, title, callback, shortcut in (("copy", "复制", self.copy, "Ctrl+C"),
                                                ("paste", "粘贴", self.paste, "Ctrl+V"),
                                                ("delete", "删除", self.delete, "Delete")):
            action = window._action(key, title, callback, shortcut)
            # 仅画布和对象树注册控件快捷键；输入框保留 Qt 自己的文字编辑。
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            window.object_tree.addAction(action)
            menu.addAction(action)
        window.object_tree.context_requested.connect(self._tree_context)
        menu.aboutToShow.connect(self.refresh)
        select_all = window._action("select_all", "全选控件", self.select_all, "Ctrl+A")
        select_all.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        window.object_tree.addAction(select_all)
        menu.addAction(select_all)
        self.arrange_menu = window.menuBar().addMenu("排版")
        for mode, label in ARRANGEMENTS.items():
            if mode in {"horizontal", "same_width"}:
                self.arrange_menu.addSeparator()
            self.arrange_menu.addAction(window._action("arrange_" + mode, label, lambda value=mode: self.arrange(value)))
        self.arrange_menu.addSeparator()
        stacking_menu = self.arrange_menu.addMenu("层级")
        for mode, label in STACKING.items():
            stacking_menu.addAction(window._action("stack_" + mode, label, lambda value=mode: self.stack(value)))
        self.arrange_menu.setToolTipsVisible(True)
        self.arrange_menu.aboutToShow.connect(self.refresh)
        QApplication.clipboard().dataChanged.connect(self.refresh)
        QApplication.instance().focusChanged.connect(self.refresh)

    def bind_canvas(self, canvas: DesignerCanvas) -> None:
        for key in ("copy", "paste", "delete", "undo", "redo", "select_all"):
            canvas.addAction(self.window.actions[key])
        canvas.context_requested.connect(lambda position, global_position:
                                        self._canvas_context(canvas, position, global_position))
        canvas.document.selection_changed.connect(self.refresh)

    def text_editor(self) -> QLineEdit | QPlainTextEdit | QTextEdit | None:
        widget = QApplication.focusWidget()
        return widget if isinstance(widget, (QLineEdit, QPlainTextEdit, QTextEdit)) and self.window.isAncestorOf(widget) else None

    def _observe_editor(self, editor: QLineEdit | QPlainTextEdit | QTextEdit | None) -> None:
        if editor is self._observed_editor:
            return
        previous = self._observed_editor
        if previous is not None:
            previous.textChanged.disconnect(self.refresh)
            previous.selectionChanged.disconnect(self.refresh)
            previous.destroyed.disconnect(self._editor_destroyed)
            if not isinstance(previous, QLineEdit):
                previous.undoAvailable.disconnect(self.refresh)
                previous.redoAvailable.disconnect(self.refresh)
        self._observed_editor = editor
        if editor is not None:
            editor.textChanged.connect(self.refresh)
            editor.selectionChanged.connect(self.refresh)
            editor.destroyed.connect(self._editor_destroyed)
            if not isinstance(editor, QLineEdit):
                editor.undoAvailable.connect(self.refresh)
                editor.redoAvailable.connect(self.refresh)

    def _editor_destroyed(self, *args: object) -> None:
        self._observed_editor = None
        defer(self, self.refresh)

    def node_states(self) -> tuple[bool, bool, bool]:
        document = self.window.document
        if document is None or document.closed:
            return False, False, False
        model, key = document.model, document.selected_id
        node = model.nodes.get(key)
        editable = not document.read_only and not document.editing_suspended
        copyable = False
        if node and not document.editing_suspended:
            try:
                roots = selected_roots(model, document.selected_ids)
                require(all(model.nodes[key].slot != "pages" for key in roots), "请复制整个选择夹。")
                for selected in subtree_ids(model, roots):
                    check_copyable(model, self.window.registry, selected, include_children=True)
                require(len({model.nodes[selected].parent_id for selected in roots}) == 1,
                        "请选择同一容器的控件。")
                copyable = True
            except DesignerError:
                pass
        deletable = bool(editable and all(model.nodes[selected].slot in {"children", "pages", "non_visual", "tool_bar", "status_bar", "menu_bar", "menu", "dock"} for selected in document.selected_ids))
        if node and node.slot == "pages" and len(pages(model, node.parent_id)) == 1:
            deletable = False
        if deletable:
            deletable = not any(model.nodes[key].designer["locked"] for selected in document.selected_ids
                                for key in ancestors(model, selected))
            children: dict[str | None, list[str]] = {}
            for child in model.nodes.values():
                children.setdefault(child.parent_id, []).append(child.id)
            pending = list(document.selected_ids)
            while pending:
                current = pending.pop()
                if model.nodes[current].designer["locked"]:
                    deletable = False
                    break
                pending.extend(children.get(current, ()))
        parent_id = self._paste_parent()
        central = model.nodes[parent_id]
        pastable = bool(editable and has_component() and not central.designer["locked"] and
                        not model.nodes[model.root_id].designer["locked"] and
                        (central.layout or {}).get("kind", "absolute") == "absolute")
        pastable = pastable and not any(model.nodes[key].designer["locked"] for key in ancestors(model, parent_id))
        return copyable, pastable, deletable

    def refresh(self, *args: object) -> None:
        if self._disposed:
            return
        editor = self.text_editor()
        self._observe_editor(editor)
        if editor is not None:
            selected = editor.hasSelectedText() if isinstance(editor, QLineEdit) else editor.textCursor().hasSelection()
            mime = QApplication.clipboard().mimeData()
            states = (selected, not editor.isReadOnly() and mime is not None and mime.hasText(), not editor.isReadOnly())
            history = editor if isinstance(editor, QLineEdit) else editor.document()
            undo = not editor.isReadOnly() and history.isUndoAvailable()
            redo = not editor.isReadOnly() and history.isRedoAvailable()
        else:
            states = self.node_states()
            document = self.window.document
            editable = bool(document and not document.closed and not document.read_only and not document.editing_suspended)
            undo = bool(editable and document.history.can_undo)
            redo = bool(editable and document.history.can_redo)
        for key, enabled in zip(("copy", "paste", "delete"), states):
            self.window.actions[key].setEnabled(enabled)
        self.window.actions["undo"].setEnabled(undo)
        self.window.actions["redo"].setEnabled(redo)
        document = self.window.document
        self.window.actions["select_all"].setEnabled(editor is not None or bool(document and not document.closed and not document.editing_suspended))
        arrangeable = False
        stacking = frozenset()
        if editor is None and document and not document.closed and not document.read_only and not document.editing_suspended:
            try:
                stacking = available_stacking(document.model, document.selected_ids)
                arrangeable = True
            except DesignerError:
                pass
        for mode in STACKING:
            self.window.actions["stack_" + mode].setEnabled(mode in stacking)
        for mode in ARRANGEMENTS:
            action = self.window.actions["arrange_" + mode]
            action.setEnabled(arrangeable and len(document.selected_ids) >= (3 if mode in {"horizontal", "vertical"} else 2))
            if mode in {"same_width", "same_height", "same_size"}:
                dimension = {"same_width": "宽度", "same_height": "高度", "same_size": "宽度和高度"}[mode]
                action.setToolTip(f"以最后选中的控件为基准，统一{dimension}，保持各控件位置；整次操作可撤销。")
            else:
                action.setToolTip("保持首尾位置，均分控件之间的空隙。" if mode in {"horizontal", "vertical"} else
                                  "以最后单击的控件为基准；排版作为一次操作撤销。")

    def select_all(self) -> None:
        editor = self.text_editor()
        if editor is not None:
            editor.selectAll()
        elif self._prepare():
            canvas = self.window.page.canvas
            model = self.window.document.model
            self.window.document.select_many(selected_roots(model, tuple(key for key, item in canvas.renderer.items.items()
                                                                         if item.isVisible() and model.nodes[key].slot == "children")))

    def arrange(self, mode: str) -> None:
        if self._prepare():
            document = self.window.document
            keys, primary = document.selected_ids, document.selected_id
            document.execute(ARRANGEMENTS[mode], lambda model: arrange_nodes(model, keys, mode, primary))
            self.window.statusBar().showMessage(f"已完成{ARRANGEMENTS[mode]}；按 Ctrl+Z 可撤销整次排版。")

    def stack(self, mode: str) -> None:
        if self._prepare():
            document = self.window.document
            keys = document.selected_ids
            document.execute(STACKING[mode], lambda model: stack_nodes(model, keys, mode))
            self.window.statusBar().showMessage(f"已完成{STACKING[mode]}；按 Ctrl+Z 可撤销。")

    def undo(self) -> None:
        self._replay(forward=False)

    def redo(self) -> None:
        self._replay(forward=True)

    def _replay(self, *, forward: bool) -> None:
        editor = self.text_editor()
        if editor is not None:
            if not editor.isReadOnly():
                editor.redo() if forward else editor.undo()
        elif self._prepare():
            document = self.window.document
            document.redo() if forward else document.undo()
        self.refresh()

    def _prepare(self) -> bool:
        if self.window.document is None:
            return False
        self.window.page.canvas.cancel_gesture()
        return self.window.properties.commit_pending()

    def copy(self) -> None:
        editor = self.text_editor()
        if editor is not None:
            editor.copy()
        else:
            self._copy_node()

    def _copy_node(self) -> None:
        if not self._prepare():
            return
        document = self.window.document
        model = document.model
        roots = selected_roots(model, document.selected_ids)
        has_descendants = len(subtree_ids(model, roots)) > len(roots)
        fragment = (copy_tree(model, self.window.registry, roots) if has_descendants else
                    copy_group(model, self.window.registry, roots) if len(roots) > 1 else
                    copy_fragment(model, self.window.registry, roots[0]))
        write_component(fragment)
        # Windows 剪贴板变更通知可能延后，立即开放本次复制对应的粘贴操作。
        self.refresh()
        description = f"{len(fragment.nodes)} 个控件" if isinstance(fragment, (GroupFragment, TreeFragment)) else f"“{fragment.node.name}”"
        message = f"已复制{description}；可在画布右键粘贴，或按 Ctrl+V。"
        if fragment.omitted_connections:
            message += f" 已跳过 {fragment.omitted_connections} 条与外部控件关联的连接（含页面关联）。"
        if fragment.handlers:
            message += " 处理函数只复制声明，不包含外部业务代码。"
        self.window.statusBar().showMessage(message)
        if fragment.omitted_connections or fragment.handlers:
            self.window.output.write_message(message)

    def paste(self) -> None:
        editor = self.text_editor()
        if editor is not None:
            if not editor.isReadOnly():
                editor.paste()
        else:
            self._paste_node()

    def _paste_parent(self, position: QPointF | None = None) -> str:
        document = self.window.document
        if position is not None:
            return self.window.page.canvas.container_at(position)
        node = document.model.nodes[document.selected_id]
        spec = document.registry.get(node.type_id)
        return active_page(document.model, node.id) if spec and spec.can_contain else node.parent_id if node.slot == "children" else document.model.central_id

    def _paste_node(self, position: QPointF | None = None) -> None:
        if not self._prepare():
            return
        document = self.window.document
        fragment = read_component(self.window.registry)
        copied_nodes = fragment.nodes if isinstance(fragment, (TreeFragment, GroupFragment)) else (fragment.node,)
        parent_id = self._paste_parent(position)
        if position is None:
            root_ids = set(fragment.roots) if isinstance(fragment, TreeFragment) else {node.id for node in copied_nodes}
            copying_container = any(node.id in root_ids and self.window.registry.require(node.type_id).can_contain for node in copied_nodes)
            selected_node = document.model.nodes[document.selected_id]
            if copying_container and selected_node.slot in {"children", "dock"}:
                # 键盘粘贴容器默认生成同级副本；在容器内部右键粘贴可明确指定嵌套目标。
                parent_id = selected_node.parent_id
        identity = (document.session_id + parent_id, fragment.id)
        count = self._paste_count + 1 if identity == self._paste_identity else 1
        created: list[str] = []
        cleared_shortcuts = []

        def transform(model: ProjectModel) -> ProjectModel:
            operation = paste_tree if isinstance(fragment, TreeFragment) else paste_group if isinstance(fragment, GroupFragment) else paste_fragment
            ox, oy = content_origin(model, parent_id)
            candidate, key = operation(model, self.window.registry, fragment,
                                            position=(round(position.x() - ox), round(position.y() - oy)) if position is not None else None,
                                            offset=count * 16, parent_id=parent_id)
            created.extend(key if isinstance(key, tuple) else (key,))
            before = sum(bool(node.properties.get("shortcut")) for node in copied_nodes)
            after = sum(bool(node.properties.get("shortcut")) for key, node in candidate.nodes.items() if key not in model.nodes)
            cleared_shortcuts.append(before - after)
            return candidate

        document.execute("粘贴控件", transform)
        self._paste_identity, self._paste_count = identity, count
        document.select_many(tuple(created))
        self.window.page.canvas.setFocus()
        message = f"已粘贴 {len(created)} 个控件；按 Delete 删除，按 Ctrl+Z 撤销。"
        if cleared_shortcuts and cleared_shortcuts[0]:
            message += f" 已清除副本中 {cleared_shortcuts[0]} 个冲突的快捷键，可在属性中重新设置。"
        self.window.statusBar().showMessage(message)

    def delete(self) -> None:
        editor = self.text_editor()
        if isinstance(editor, QLineEdit):
            if not editor.isReadOnly():
                editor.del_()
        elif editor is not None:
            if not editor.isReadOnly():
                cursor = editor.textCursor()
                cursor.deleteChar()
        else:
            self._delete_node()

    def _delete_node(self) -> None:
        if self._prepare():
            self.window.page.canvas.delete_selected()

    def _canvas_context(self, canvas: DesignerCanvas, position: QPoint | None, global_position: QPoint) -> None:
        if self.window.page is None or self.window.page.canvas is not canvas or not canvas.ready:
            return
        if not self._prepare():
            return
        if position is not None:
            key = canvas.node_at(position)
            if key not in canvas.document.selected_ids:
                canvas.document.select(key)
        canvas.setFocus()
        scene_position = canvas.mapToScene(position) if position is not None else None
        self._show_context(global_position, scene_position)

    def _tree_context(self, node_id: str, global_position: QPoint) -> None:
        if not self._prepare():
            return
        document = self.window.document
        key = node_id or document.model.root_id
        if key not in document.selected_ids:
            document.select(key)
        self.window.object_tree.setFocus()
        self._show_context(global_position)

    def _show_context(self, global_position: QPoint, position: QPointF | None = None) -> None:
        if self.menu:
            self.menu.close()
        document = self.window.document
        selected, revision = document.selected_ids, document.revision
        primary = document.selected_id
        menu = QMenu(self.window)
        menu.setObjectName("componentContextMenu")
        self.menu = menu
        copyable, pastable, deletable = self.node_states()

        def run(operation: Callable[[], object]) -> None:
            def checked() -> None:
                require(self.window.document is document and not document.closed and
                        document.selected_ids == selected and document.selected_id == primary and document.revision == revision,
                        "菜单对应的设计内容已变化，请重新打开右键菜单。")
                operation()
            self.window._guard(checked)

        for key, title, shortcut, callback, enabled in (
            ("copy", "复制", "Ctrl+C", self._copy_node, copyable),
            ("paste", "粘贴", "Ctrl+V", lambda: self._paste_node(position), pastable),
            ("delete", "删除", "Delete", self._delete_node, deletable),
        ):
            action = menu.addAction(title)
            action.setObjectName(key)
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
            action.setEnabled(enabled)
            action.triggered.connect(lambda checked=False, operation=callback: run(operation))
        menu.addSeparator()
        node = document.model.nodes[primary]
        if node.slot in {"root", "menu_bar", "menu"}:
            action = menu.addAction("编辑菜单…")
            action.setEnabled(not document.read_only and not document.editing_suspended)
            action.triggered.connect(lambda: run(self.window.edit_menus))
            menu.addSeparator()
        tab_id = node.id if node.type_id in PAGE_TYPES else node.parent_id if node.slot == "pages" else None
        if tab_id and len(selected) == 1:
            from core.commands.pages import add_page
            from core.commands.nodes import delete_node

            def append_page() -> None:
                created: list[str] = []
                def change(model: ProjectModel) -> ProjectModel:
                    candidate, key = add_page(model, document.registry, tab_id)
                    created.append(key)
                    from core.commands.nodes import set_property
                    return set_property(candidate, document.registry, tab_id, "current_index", len(pages(candidate, tab_id)) - 1)
                document.execute("添加选择夹页面", change)
                document.select(created[0])

            add_action = menu.addAction("添加页面")
            add_action.setEnabled(not document.read_only and not document.editing_suspended)
            add_action.triggered.connect(lambda: run(append_page))
            delete_action = menu.addAction("删除当前页及其控件")
            delete_action.setEnabled(not document.read_only and len(pages(document.model, tab_id)) > 1)
            page_key = primary if node.slot == "pages" else active_page(document.model, tab_id)
            delete_action.triggered.connect(lambda: run(lambda: document.execute("删除选择夹页面", lambda model: delete_node(model, page_key))))
            menu.addSeparator()
        if len(selected) == 1 and document.model.nodes[primary].slot == "children":
            containers = menu.addMenu("移入容器")
            for node in document.model.nodes.values():
                spec = document.registry.get(node.type_id)
                if not spec or not spec.can_contain or node.type_id in PAGE_TYPES or node.id == primary or primary in ancestors(document.model, node.id):
                    continue
                action = containers.addAction(node.name)
                action.setData(node.id)
                allowed = node.id != document.model.nodes[primary].parent_id
                try:
                    require_container(document.model, document.registry, node.id)
                except DesignerError:
                    allowed = False
                action.setEnabled(allowed and not document.read_only and not document.editing_suspended)
                action.triggered.connect(lambda checked=False, parent_id=node.id:
                    run(lambda: document.execute("调整所属容器", lambda model: reparent_node(model, document.registry, primary, parent_id))))
            menu.addSeparator()
        self.refresh()
        if any(self.window.actions["stack_" + mode].isEnabled() for mode in STACKING):
            submenu = menu.addMenu("层级")
            for mode, label in STACKING.items():
                action = submenu.addAction(label)
                action.setObjectName("stack_" + mode)
                action.setEnabled(self.window.actions["stack_" + mode].isEnabled())
                action.triggered.connect(lambda checked=False, value=mode: run(lambda: self.stack(value)))
            menu.addSeparator()
        if len(selected) > 1:
            submenu = menu.addMenu("排版")
            submenu.setToolTipsVisible(True)
            for mode, label in ARRANGEMENTS.items():
                if mode in {"horizontal", "same_width"}:
                    submenu.addSeparator()
                action = submenu.addAction(label)
                action.setObjectName("arrange_" + mode)
                source = self.window.actions["arrange_" + mode]
                action.setEnabled(source.isEnabled())
                action.setToolTip(source.toolTip())
                action.triggered.connect(lambda checked=False, value=mode: run(lambda: self.arrange(value)))
            menu.addSeparator()
        for key, title, callback in (("undo", "撤销", document.undo), ("redo", "重做", document.redo)):
            action = menu.addAction(title)
            action.setObjectName(key)
            action.setEnabled(self.window.actions[key].isEnabled())
            action.triggered.connect(lambda checked=False, operation=callback: run(operation))
        menu.addSeparator()
        action = menu.addAction("窗口属性")
        action.triggered.connect(lambda: run(self.window.select_window))

        def release() -> None:
            if self.menu is menu:
                self.menu = None
            menu.deleteLater()

        menu.aboutToHide.connect(release)
        menu.popup(global_position)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        self._observe_editor(None)
        if self.menu:
            self.menu.close()
        QApplication.clipboard().dataChanged.disconnect(self.refresh)
        QApplication.instance().focusChanged.disconnect(self.refresh)
