"""使用真实文件模型核对项目筛选、目录切换、选择及取消。"""

from pathlib import Path
from time import monotonic

import pytest
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QFileSystemModel, QLineEdit, QListView, QTreeView, QToolButton

from app.main_window import MainWindow
from core.models import new_project
from core.storage import commit_project, load_project
from tests.test_appearance import designed_window


def wait_for(predicate, message):
    deadline = monotonic() + 4
    while not predicate() and monotonic() < deadline:
        QTest.qWait(10)
    assert predicate(), message() if callable(message) else message


def names(dialog):
    model = dialog.findChild(QFileSystemModel)
    root = model.index(dialog.directory().absolutePath())
    return {model.fileName(model.index(row, 0, root)) for row in range(model.rowCount(root))}


def use_dialog(invoke, inspect):
    errors = []
    visited = []

    def interact():
        dialog = QApplication.activeModalWidget()
        try:
            assert isinstance(dialog, QFileDialog)
            visited.append(dialog)
            inspect(dialog)
        except BaseException as exc:
            errors.append(exc)
        finally:
            if isinstance(dialog, QFileDialog) and dialog.isVisible():
                dialog.reject()

    QTimer.singleShot(0, interact)
    result = invoke()
    if errors:
        raise errors[0]
    assert visited, "没有打开文件对话框。"
    return result


@pytest.fixture
def project_folder(tmp_path):
    folder = tmp_path / "中文项目 (演示)"
    folder.mkdir()
    commit_project(folder / "库存管理台.uipro", new_project("库存管理台"), expected_token=None)
    commit_project(folder / "账号 登录.UIPRO", new_project("账号登录"), expected_token=None)
    (folder / "说明.txt").write_text("不是设计项目", encoding="utf-8")
    (folder / "旧项目.uipro.bak").write_text("备份", encoding="utf-8")
    (folder / "子目录").mkdir()
    return folder


@pytest.mark.parametrize("view_mode", [QFileDialog.ViewMode.List, QFileDialog.ViewMode.Detail])
def test_open_projects_remain_visible_after_reentering_folder(designed_window, project_folder, view_mode):
    window = designed_window
    window.settings.setValue("files/default_directory", str(project_folder))
    expected = {"库存管理台.uipro", "账号 登录.UIPRO", "子目录"}

    def inspect(dialog):
        dialog.setViewMode(view_mode)
        model = dialog.findChild(QFileSystemModel)
        assert model.nameFilters() == ["*.uipro"], "项目扩展名没有被解析为文件过滤规则。"
        for _ in range(6):
            dialog.setDirectory(str(project_folder.parent))
            wait_for(lambda: project_folder.name in names(dialog), "上级目录未列出项目文件夹。")
            dialog.setDirectory(str(project_folder))
            wait_for(lambda: names(dialog) == expected, f"项目文件列表错误：{names(dialog)}")
        view = dialog.findChild(QListView, "listView") if view_mode == QFileDialog.ViewMode.List else dialog.findChild(QTreeView, "treeView")
        index = model.index(str(project_folder / "库存管理台.uipro"))
        view.scrollTo(index)
        QTest.qWait(20)
        QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=view.visualRect(index).center())
        assert dialog.selectedFiles() == [str(project_folder / "库存管理台.uipro").replace("\\", "/")]
        dialog.accept()

    use_dialog(window.open_dialog, inspect)
    assert window.document.path == (project_folder / "库存管理台.uipro").resolve()
    assert window.document.model.name == "库存管理台"


def test_open_all_files_filter_and_cancel_keep_current_document(designed_window, project_folder):
    window = designed_window
    window.settings.setValue("files/default_directory", str(project_folder))
    document, count = window.document, window.tabs.count()

    def inspect(dialog):
        all_files = next(item for item in dialog.nameFilters() if item.endswith("(*)"))
        dialog.selectNameFilter(all_files)
        wait_for(lambda: "说明.txt" in names(dialog), "所有文件筛选未显示其他文件。")
        dialog.selectNameFilter(dialog.nameFilters()[0])
        wait_for(lambda: names(dialog) == {"库存管理台.uipro", "账号 登录.UIPRO", "子目录"},
                 "切换回项目筛选后文件列表不正确。")
        dialog.reject()

    use_dialog(window.open_dialog, inspect)
    assert window.document is document and window.tabs.count() == count


def test_reopen_and_double_click_folder_after_parent_navigation(designed_window, project_folder):
    window = designed_window
    window.settings.setValue("files/default_directory", str(project_folder.parent))

    def inspect(dialog):
        dialog.setViewMode(QFileDialog.ViewMode.List)
        model = dialog.findChild(QFileSystemModel)
        view = dialog.findChild(QListView, "listView")
        loaded = []
        model.directoryLoaded.connect(loaded.append)
        for iteration in range(4):
            wait_for(lambda: project_folder.name in names(dialog),
                     lambda: f"第 {iteration + 1} 轮：父目录未显示示例目录；当前路径 {dialog.directory().absolutePath()}；"
                             f"当前内容 {names(dialog)}；上一级按钮可用 {dialog.findChild(QToolButton, 'toParentButton').isEnabled()}；"
                             f"已加载 {loaded}；过滤 {model.filter()}；根路径 {model.rootPath()}；"
                             f"根有效 {model.index(model.rootPath()).isValid()}；待加载 {model.canFetchMore(model.index(model.rootPath()))}；"
                             f"视图根 {model.filePath(view.rootIndex())}；视图行数 {model.rowCount(view.rootIndex())}；"
                             f"实际文件 {[path.name for path in Path(model.rootPath()).iterdir()]}")
            index = model.index(str(project_folder))
            view.scrollTo(index)
            QTest.qWait(20)
            point = view.visualRect(index).center()
            QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=point)
            QTest.mouseDClick(view.viewport(), Qt.MouseButton.LeftButton, pos=point)
            wait_for(lambda: "库存管理台.uipro" in names(dialog), "双击进入目录后项目文件未显示。")
            QTest.mouseClick(dialog.findChild(QToolButton, "toParentButton"), Qt.MouseButton.LeftButton)
        dialog.reject()

    for _ in range(3):
        use_dialog(window.open_dialog, inspect)


def test_save_project_dialog_lists_existing_projects_and_cancel_keeps_state(designed_window, project_folder):
    window = designed_window
    window.settings.setValue("files/default_directory", str(project_folder))
    document = window.document
    before = document.model.to_bytes()

    def inspect(dialog):
        assert dialog.acceptMode() == QFileDialog.AcceptMode.AcceptSave
        assert dialog.findChild(QFileSystemModel).nameFilters() == ["*.uipro"]
        wait_for(lambda: "库存管理台.uipro" in names(dialog), "保存窗口未显示已有项目。")
        dialog.reject()

    assert use_dialog(window.save_current, inspect) is False
    assert document.path is None and not document.saving and document.model.to_bytes() == before


def test_save_new_project_adds_extension_and_writes_correct_document(designed_window, project_folder):
    window = designed_window
    window.settings.setValue("files/default_directory", str(project_folder))
    document = window.document
    expected = document.model.to_bytes()
    target = project_folder / "新保存项目.uipro"

    def inspect(dialog):
        dialog.findChild(QLineEdit, "fileNameEdit").setText("新保存项目")
        dialog.accept()

    assert use_dialog(window.save_current, inspect) is True
    wait_for(lambda: not document.saving, "保存操作未结束。")
    assert document.path == target.resolve()
    assert load_project(target).model.to_bytes() == expected


def test_diagnostic_dialog_lists_zip_files(designed_window, tmp_path):
    archive = tmp_path / "已有诊断.zip"
    archive.write_bytes(b"PK")
    (tmp_path / "说明.txt").write_text("说明", encoding="utf-8")

    def inspect(dialog):
        assert dialog.findChild(QFileSystemModel).nameFilters() == ["*.zip"]
        dialog.setDirectory(str(tmp_path))
        wait_for(lambda: "已有诊断.zip" in names(dialog), "诊断导出窗口未显示已有压缩包。")
        assert "说明.txt" not in names(dialog)
        dialog.reject()

    use_dialog(designed_window.export_diagnostics_dialog, inspect)
    assert archive.read_bytes() == b"PK"
