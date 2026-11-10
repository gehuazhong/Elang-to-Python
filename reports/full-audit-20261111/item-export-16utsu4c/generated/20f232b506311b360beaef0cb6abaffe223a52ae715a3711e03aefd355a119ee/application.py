"""设计预览与导出应用共用的中文运行外观，不依赖设计器工作台。"""

from __future__ import annotations

from PySide6.QtCore import QFileInfo, QLibraryInfo, QLocale, QTranslator
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QFileDialog, QFileIconProvider, QToolButton


class ChineseTranslator(QTranslator):
    """补齐当前 Qt 翻译包中仍使用英文的公共对话框文字。"""

    def translate(self, context: str, source_text: str, disambiguation: str | None = None, n: int = -1) -> str:
        labels = {"Look in:": "查找位置：", "Files of type:": "文件类型：", "File name:": "文件名称：",
                  "Back": "后退", "Forward": "前进", "Parent Directory": "上一级目录", "Create New Folder": "新建文件夹",
                  "List View": "列表视图", "Detail View": "详细信息", "&HTML:": "颜色代码：", "HTML:": "颜色代码："}
        return labels[source_text] if source_text in labels else super().translate(context, source_text, disambiguation, n)


class ChineseFileIconProvider(QFileIconProvider):
    def type(self, info: QFileInfo) -> str:
        if info.isDir():
            return "文件夹"
        return (info.suffix().upper() + " 文件") if info.suffix() else "文件"


def configure_file_dialog(dialog: QFileDialog) -> None:
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    for key, text in ((QFileDialog.DialogLabel.LookIn, "查找位置："), (QFileDialog.DialogLabel.FileName, "文件名称："),
                      (QFileDialog.DialogLabel.FileType, "文件类型："), (QFileDialog.DialogLabel.Reject, "取消")):
        dialog.setLabelText(key, text)
    provider = ChineseFileIconProvider()
    dialog.setIconProvider(provider)
    dialog._chinese_icon_provider = provider
    tips = {"backButton": "后退", "forwardButton": "前进", "toParentButton": "上一级目录",
            "newFolderButton": "新建文件夹", "listModeButton": "列表视图", "detailModeButton": "详细信息"}
    for button in dialog.findChildren(QToolButton):
        if button.objectName() in tips:
            button.setToolTip(tips[button.objectName()])


def configure_application(application: QApplication) -> None:
    application.setStyle("Fusion")
    palette = application.style().standardPalette()
    for role, color in ((QPalette.ColorRole.Window, "#f4f6f8"),
                        (QPalette.ColorRole.WindowText, "#243444"),
                        (QPalette.ColorRole.Base, "#ffffff"),
                        (QPalette.ColorRole.AlternateBase, "#f7f9fb"),
                        (QPalette.ColorRole.Text, "#243444"),
                        (QPalette.ColorRole.Button, "#f0f3f6"),
                        (QPalette.ColorRole.ButtonText, "#243444"),
                        (QPalette.ColorRole.Highlight, "#477bca"),
                        (QPalette.ColorRole.HighlightedText, "#ffffff"),
                        (QPalette.ColorRole.PlaceholderText, "#718090")):
        palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#8491a0"))
    application.setPalette(palette)
    application.setFont(QFont("Microsoft YaHei UI", 10))
    QLocale.setDefault(QLocale(QLocale.Language.Chinese, QLocale.Country.China))
    translator = ChineseTranslator(application)
    translations = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if not translator.load("qtbase_zh_CN", translations):
        translator.deleteLater()
        raise RuntimeError("缺少 Qt 中文翻译文件，请重新安装规定版本的 PySide6。")
    previous = getattr(application, "_chinese_translator", None)
    if previous is not None:
        application.removeTranslator(previous)
        previous.deleteLater()
    application.installTranslator(translator)
    application._chinese_translator = translator
