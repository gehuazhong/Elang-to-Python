"""Nonblocking native dialogs with a consistent result signal."""

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QMessageBox, QErrorMessage, QInputDialog, QColorDialog,
                               QFontDialog, QProgressDialog, QLineEdit)
from shiboken6 import isValid
from .advanced_containers import TriggerWindow, BUTTONS


class DialogService(QObject, TriggerWindow):
    accepted = Signal(object)
    cancelled = Signal()
    native_class = QMessageBox

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = {}
        self.native = None
        self.design_mode = True

    def configure(self, values):
        self.values = values

    def open_dialog(self, checked=False):
        if self.design_mode:
            return
        if self.native is not None and isValid(self.native) and not self.native._uiplay_settled:
            self.native.show()
            self.native.raise_()
            return
        if self.native is not None:
            self._release_native(self.native)
        v = self.values
        dialog = self.native_class(self.parent())
        self.native = dialog
        dialog._uiplay_settled = False
        dialog.destroyed.connect(self._native_destroyed)
        dialog.setWindowTitle(v["title"])
        dialog.setModal(v.get("modal", False))
        if isinstance(dialog, QMessageBox):
            from PySide6.QtCore import Qt
            dialog.setTextFormat(Qt.TextFormat.RichText if v.get("text_format") == "rich" else Qt.TextFormat.PlainText)
            dialog.setText(v["text"])
            dialog.setInformativeText(v.get("informative_text", ""))
            dialog.setDetailedText(v.get("detailed_text", ""))
            dialog.setIcon(getattr(QMessageBox.Icon, v["icon_kind"].capitalize()))
            flags = QMessageBox.StandardButton.NoButton
            for name in v["buttons"]:
                flags |= QMessageBox.StandardButton(BUTTONS[name].value)
            dialog.setStandardButtons(flags)
            for name in v["buttons"]:
                dialog.button(QMessageBox.StandardButton(BUTTONS[name].value)).setText(name)
            if v.get("default_button", "auto") != "auto":
                dialog.setDefaultButton(QMessageBox.StandardButton(BUTTONS[v["default_button"]].value))
        elif isinstance(dialog, QInputDialog):
            dialog.setLabelText(v["label"])
            mode = {"text": QInputDialog.InputMode.TextInput, "integer": QInputDialog.InputMode.IntInput,
                    "decimal": QInputDialog.InputMode.DoubleInput}[v["input_mode"]]
            dialog.setInputMode(mode)
            if v.get("input_items"):
                dialog.setComboBoxItems(list(v["input_items"]))
                dialog.setComboBoxEditable(v.get("items_editable", False))
            dialog.setTextValue(v["text_value"])
            dialog.setTextEchoMode(QLineEdit.EchoMode.Password if v["password"] else QLineEdit.EchoMode.Normal)
            dialog.setIntRange(int(v["minimum"]), int(v["maximum"]))
            dialog.setIntValue(int(v["value"]))
            dialog.setDoubleDecimals(v["decimals"])
            dialog.setDoubleRange(v["minimum"], v["maximum"])
            dialog.setDoubleValue(v["value"])
            dialog.setIntStep(v.get("integer_step", 1))
            dialog.setDoubleStep(v.get("decimal_step", 1.0))
            dialog.setOption(QInputDialog.InputDialogOption.UsePlainTextEditForTextInput, v.get("multiline", False))
            # Value setters select their respective input mode internally.
            dialog.setInputMode(mode)
            dialog.setOkButtonText(v.get("ok_text", "确定"))
            dialog.setCancelButtonText(v.get("cancel_text", "取消"))
        elif isinstance(dialog, QColorDialog):
            dialog.setCurrentColor(QColor(v["initial_color"]))
            dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, v["alpha_channel"])
            dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, not v.get("use_native_dialog", True))
        elif isinstance(dialog, QFontDialog):
            font = QFont(v["font_family"]) if v["font_family"] else QFont()
            font.setPointSize(v["font_size"])
            dialog.setCurrentFont(font)
            dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, not v.get("use_native_dialog", True))
            filters = {"scalable": "ScalableFonts", "non_scalable": "NonScalableFonts",
                       "monospace": "MonospacedFonts", "proportional": "ProportionalFonts"}
            if v.get("font_filter", "all") != "all":
                dialog.setOption(getattr(QFontDialog.FontDialogOption, filters[v["font_filter"]]), True)
        elif isinstance(dialog, QProgressDialog):
            dialog.setLabelText(v["text"])
            dialog.setCancelButtonText(v["cancel_text"])
            dialog.setRange(v["minimum"], v["maximum"])
            dialog.setAutoClose(v["auto_close"])
            dialog.setAutoReset(v.get("auto_reset", True))
            dialog.setMinimumDuration(0)
            dialog.setValue(v["value"])
            dialog.canceled.connect(self._progress_cancelled)
        dialog.finished.connect(self._finished)
        if isinstance(dialog, QErrorMessage):
            dialog.showMessage(v["text"])
        else:
            dialog.show()

    @Slot(int)
    def _finished(self, result):
        dialog = self.sender()
        if dialog is not self.native or dialog is None:
            return
        value = result
        if isinstance(dialog, QMessageBox):
            accepted = result not in {0, QMessageBox.StandardButton.Cancel.value, QMessageBox.StandardButton.No.value,
                                      QMessageBox.StandardButton.Close.value}
        else:
            accepted = bool(result)
        if accepted:
            if isinstance(dialog, QInputDialog):
                value = {QInputDialog.InputMode.TextInput: dialog.textValue,
                         QInputDialog.InputMode.IntInput: dialog.intValue,
                         QInputDialog.InputMode.DoubleInput: dialog.doubleValue}[dialog.inputMode()]()
            elif isinstance(dialog, QColorDialog):
                value = dialog.currentColor().name(QColor.NameFormat.HexArgb)
            elif isinstance(dialog, QFontDialog):
                value = dialog.currentFont().toString()
            elif isinstance(dialog, QProgressDialog):
                value = dialog.value()
        self._settle(dialog, accepted, value)

    def _release_native(self, dialog):
        if self.native is dialog:
            self.native = None
        if isValid(dialog):
            dialog.hide()
            dialog.deleteLater()

    def _settle(self, dialog, accepted, value=None, *, keep_open=False):
        if dialog is not self.native or not isValid(dialog):
            return
        if dialog._uiplay_settled:
            if not keep_open:
                self._release_native(dialog)
            return
        dialog._uiplay_settled = True
        # Detach the completed dialog before business callbacks can open another.
        if not keep_open:
            self._release_native(dialog)
        if accepted:
            self.accepted.emit(value)
        else:
            self.cancelled.emit()

    @Slot()
    def _progress_cancelled(self):
        dialog = self.sender()
        if dialog is self.native and dialog is not None:
            self._settle(dialog, False)

    @Slot()
    def _native_destroyed(self):
        if self.native is not None and not isValid(self.native):
            self.native = None

    def setValue(self, value):
        dialog = self.native
        if isinstance(dialog, QProgressDialog) and isValid(dialog) and not dialog._uiplay_settled:
            minimum, maximum = dialog.minimum(), dialog.maximum()
            dialog.setValue(value)
            if value == maximum and (minimum, maximum) != (0, 0):
                self._settle(dialog, True, value, keep_open=not dialog.autoClose() if isValid(dialog) else False)

    def dispose(self):
        self.bind_trigger(None)
        dialog, self.native = self.native, None
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()


class MessageBox(DialogService):
    native_class = QMessageBox


class ErrorMessage(DialogService):
    native_class = QErrorMessage


class InputDialog(DialogService):
    native_class = QInputDialog


class ColorDialog(DialogService):
    native_class = QColorDialog


class FontDialog(DialogService):
    native_class = QFontDialog


class ProgressDialog(DialogService):
    native_class = QProgressDialog


DIALOG_FACTORIES = {cls.native_class.__name__: cls for cls in
                    (MessageBox, ErrorMessage, InputDialog, ColorDialog, FontDialog, ProgressDialog)}
