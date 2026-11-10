"""库存列表的本地筛选与行选择，不连接数据库。"""


def initialize(window):
    window.controls["search"].setFocus()


def dispatch(window, control, event, arguments):
    controls = window.controls
    table = controls["stock_list"]
    if control == "stock_list":
        selected = table.selectedItems()
        text = "选择一行查看物品信息"
        if selected and not selected[0].isHidden():
            item = selected[0]
            text = f"{item.text(0)}  /  {item.text(1)}  /  库位 {item.text(4)}  /  当前库存 {item.text(3)} 件"
        controls["selection"].setText(text)
        return
    if control == "reset_button":
        controls["search"].clear()
        controls["category"].setCurrentIndex(0)
        controls["low_only"].setChecked(False)
    keyword = controls["search"].text().strip().casefold()
    category = controls["category"].currentText()
    low_only = controls["low_only"].isChecked()
    visible = 0
    for row in range(table.topLevelItemCount()):
        item = table.topLevelItem(row)
        matches = (keyword in " ".join(item.text(column) for column in (0, 1, 4)).casefold()
                   and (category == "全部分类" or item.text(2) == category)
                   and (not low_only or int(item.text(3)) < 10))
        item.setHidden(not matches)
        visible += int(matches)
    controls["result"].setText(f"共 {visible} 项 · 低库存阈值：10 件")
    if table.currentItem() and table.currentItem().isHidden():
        table.clearSelection()
        controls["selection"].setText("选择一行查看物品信息")

