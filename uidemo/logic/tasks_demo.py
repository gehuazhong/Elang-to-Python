"""使用内存状态和 Qt 时钟模拟任务，无网络和文件下载。"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QTableWidgetItem


class TaskDemo:
    def __init__(self, window):
        self.controls = window.controls
        self.table = self.controls["task_table"]
        self.active_id = None
        self.next_id = max((int(self.table.item(row, 0).text()) for row in range(self.table.rowCount())), default=0) + 1
        self.timer = QTimer(window)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.advance)

    def selection(self):
        row = self.table.currentRow()
        if row < 0:
            self.controls["active_task"].setText("选择一个任务查看进度")
            self.controls["progress"].setValue(0)
            self.controls["progress_caption"].setText("点击列表中的任务")
            return
        self.controls["active_task"].setText(self.table.item(row, 1).text())
        progress = int(self.table.item(row, 3).text().rstrip("%"))
        self.controls["progress"].setValue(progress)
        state = self.table.item(row, 4).text()
        self.controls["progress_caption"].setText(f"{state} · {progress}% · 本地模拟")

    def count(self):
        done = sum(self.table.item(row, 4).text() == "已完成" for row in range(self.table.rowCount()))
        self.controls["queue_count"].setText(f"{self.table.rowCount()} 个任务  /  {done} 个已完成")

    def add(self):
        name = self.controls["task_name"].text().strip()
        if not name:
            self.controls["notice"].setText("请先输入任务名称，例如：产品图册.pdf")
            self.controls["task_name"].setFocus()
            return
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, value in enumerate((f"{self.next_id:02}", name, "演示任务", "0%", "等待中")):
            self.table.setItem(row, column, QTableWidgetItem(value))
        self.next_id += 1
        self.table.selectRow(row)
        self.controls["task_name"].clear()
        self.controls["notice"].setText(f"已添加“{name}”。点击“开始 / 暂停”运行模拟进度。")
        self.count()

    def toggle(self):
        row = self.table.currentRow()
        if row < 0:
            self.controls["notice"].setText("请先选择一个任务。")
            return
        identity = self.table.item(row, 0).text()
        if self.table.item(row, 4).text() == "已完成":
            self.controls["notice"].setText("所选任务已完成，可以清理或选择其他任务。")
            return
        if identity == self.active_id:
            self.timer.stop()
            self.active_id = None
            self.table.item(row, 4).setText("已暂停")
        else:
            for other in range(self.table.rowCount()):
                if self.table.item(other, 4).text() == "进行中":
                    self.table.item(other, 4).setText("已暂停")
            self.active_id = identity
            self.table.item(row, 4).setText("进行中")
            self.timer.start()
        self.controls["notice"].setText("本地模拟任务；不会连接网络或下载文件。")
        self.selection()

    def advance(self):
        row = next((row for row in range(self.table.rowCount())
                    if self.table.item(row, 0).text() == self.active_id), None)
        if row is None:
            self.timer.stop()
            self.active_id = None
            return
        progress = min(100, int(self.table.item(row, 3).text().rstrip("%")) + 4)
        self.table.item(row, 3).setText(f"{progress}%")
        if progress == 100:
            self.table.item(row, 4).setText("已完成")
            self.timer.stop()
            self.active_id = None
            self.count()
            self.controls["notice"].setText("模拟任务已完成。可选择下一个任务继续。")
        self.selection()

    def clear(self):
        for row in reversed(range(self.table.rowCount())):
            if self.table.item(row, 4).text() == "已完成":
                self.table.removeRow(row)
        self.count()
        self.selection()


def initialize(window):
    window._task_demo = TaskDemo(window)
    if window.controls["task_table"].rowCount():
        window.controls["task_table"].selectRow(0)


def dispatch(window, control, event, arguments):
    demo = getattr(window, "_task_demo", None)
    if demo is None:
        return
    if control in {"add_task", "task_name"}:
        demo.add()
    elif control == "toggle_task":
        demo.toggle()
    elif control == "clear_done":
        demo.clear()
    elif control == "task_table":
        demo.selection()

