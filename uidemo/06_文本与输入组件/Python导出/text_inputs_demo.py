"""富文本同步预览、字体选择、分组选项和保存快捷键的演示业务。"""

from PySide6.QtGui import QKeySequence


def update_preview(window):
    c = window.controls
    c["reader"].setHtml(c["editor"].toHtml())
    c["reader"].append('<p><a href="demo:restore">恢复示例内容</a></p>')
    c["statistics"].setText(f"正文 {len(c['editor'].toPlainText())} 字 · 支持富文本粘贴与撤销")


def initialize(window):
    window._initial_text = window.controls["editor"].toHtml()
    window._draft_html = None
    window._draft_count = 0
    update_preview(window)


def dispatch(window, control, event, arguments):
    c = window.controls
    if control == "editor":
        update_preview(window)
    elif control in {"font_picker", "font_size"}:
        font = c["font_picker"].currentFont()
        font.setPointSize(c["font_size"].value())
        c["editor"].setFont(font)
        c["reader"].setFont(font)
        update_preview(window)
    elif control in {"options", "read_only"}:
        c["editor"].setReadOnly(c["options"].isChecked() and c["read_only"].isChecked())
    elif control == "shortcut_input":
        sequence = c["shortcut_input"].keySequence().toString(QKeySequence.SequenceFormat.NativeText)
        c["message"].setText(f"已录入 {sequence or '空快捷键'}，点击“应用快捷键”生效。")
    elif control == "apply_shortcut":
        sequence = c["shortcut_input"].keySequence()
        c["save_draft"].setShortcut(sequence)
        c["message"].setText("保存快捷键已设为：" + (sequence.toString(QKeySequence.SequenceFormat.NativeText) or "无"))
    elif control == "save_draft":
        window._draft_html = c["editor"].toHtml()
        window._draft_count += 1
        c["message"].setText(f"第 {window._draft_count} 次保存：已保留本次运行的草稿，关闭窗口后清除。")
    elif control == "reader" and arguments[0].toString() == "demo:restore":
        c["editor"].setHtml(window._initial_text)
        c["message"].setText("已恢复示例正文。")
    elif control == "help_link":
        c["message"].setText("左侧编辑、右侧同步；可选择字体、录入保存快捷键，或点击预览中的恢复链接。")
