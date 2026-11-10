"""Editable Qt model views; models and undo stacks remain public for business code."""

from PySide6.QtGui import QStandardItem, QStandardItemModel, QUndoStack, QIcon, QPixmap
from .easy_widgets import decoded_image
from .widget_properties import apply_column_widths
from PySide6.QtWidgets import (QListView, QTableView, QTreeView, QColumnView, QUndoView,
                               QAbstractItemView, QTabBar, QButtonGroup)


class ModelView:
    def configure(self, values):
        def tree_key(entries):
            return tuple((entry["text"], tree_key(entry["children"])) for entry in entries)

        if "items" in values:
            content = tuple(values["items"])
        elif "table_data" in values:
            data = values["table_data"]
            content = (tuple(data["headers"]), tuple(tuple(row) for row in data["rows"]))
        else:
            content = tree_key(values["tree_data"])
        rebuild = (not hasattr(self, "_content_key") or self._content_key != content
                   or self.model() is not getattr(self, "data_model", None))
        if rebuild:
            model = QStandardItemModel(self)
            if "items" in values:
                for text in values["items"]:
                    model.appendRow(QStandardItem(text))
            elif "table_data" in values:
                model.setHorizontalHeaderLabels(list(data["headers"]))
                for row in data["rows"]:
                    model.appendRow([QStandardItem(text) for text in row])
            else:
                def append(parent, entries):
                    for entry in entries:
                        item = QStandardItem(entry["text"])
                        parent.appendRow(item)
                        append(item, entry["children"])
                append(model.invisibleRootItem(), values["tree_data"])
            previous, selection = self.model(), self.selectionModel()
            owned_selection = selection is not None and selection.parent() is self
            self.setModel(model)
            self.data_model, self._content_key = model, content
            # QColumnView keeps its old, view-owned selection model after setModel.
            if owned_selection and selection is not self.selectionModel():
                selection.deleteLater()
            if previous is not None and previous.parent() is self:
                previous.deleteLater()
        if "items" in values:
            self.setViewMode(QListView.ViewMode.IconMode if values["view_mode"] == "icons" else QListView.ViewMode.ListMode)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
                             if values["editable"] else QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode({"single": QAbstractItemView.SelectionMode.SingleSelection,
                               "extended": QAbstractItemView.SelectionMode.ExtendedSelection,
                               "none": QAbstractItemView.SelectionMode.NoSelection}[values["selection_mode"]])
        self.setAlternatingRowColors(values["alternating"])
        if "table_data" in values:
            apply_column_widths(self.horizontalHeader(), values["table_data"], 100, True)
        if "sorting" in values:
            self.setSortingEnabled(values["sorting"])
        if rebuild and isinstance(self, QTreeView):
            self.expandAll()


class ListView(QListView, ModelView):
    pass


class TableView(QTableView, ModelView):
    pass


class TreeView(QTreeView, ModelView):
    pass


class ColumnView(QColumnView, ModelView):
    pass


class UndoView(QUndoView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.undo_stack = QUndoStack(self)
        self.setStack(self.undo_stack)

    def configure(self, values):
        self.setEmptyLabel(values["empty_label"])
        self.setCleanIcon(QIcon(QPixmap.fromImage(decoded_image(values["clean_icon"]))))


class TabBar(QTabBar):
    def configure(self, values):
        while self.count():
            self.removeTab(0)
        for text in values["items"]:
            self.addTab(text)
        self.setCurrentIndex(values["current_index"])
        self.setTabsClosable(values["tabs_closable"])
        self.setMovable(values["movable"])
        self.setExpanding(values["expanding"])


class ButtonGroup(QButtonGroup):
    def configure(self, values):
        self.values = values
        self.setExclusive(values["exclusive"])


VIEW_FACTORIES = {"QListView": ListView, "QTableView": TableView, "QTreeView": TreeView,
                  "QColumnView": ColumnView, "QUndoView": UndoView, "QTabBar": TabBar,
                  "QButtonGroup": ButtonGroup}
