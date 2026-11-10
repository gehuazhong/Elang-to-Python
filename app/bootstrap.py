"""初始化日志、中文翻译和已核验的控件注册表。"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication

from core.errors import DesignerError
from runtime.application import configure_application
from .diagnostics import configure_file_logging
from .designer_theme import install_designer_theme
from .version import VERSION


def initialize(application: QApplication, *, configure_logging: bool = True) -> Path:
    application.setOrganizationName("中文界面工具")
    application.setApplicationName("中文界面设计器")
    application.setApplicationDisplayName("中文界面设计器")
    application.setApplicationVersion(VERSION)
    try:
        configure_application(application)
        install_designer_theme(application)
    except RuntimeError as exc:
        raise DesignerError(str(exc)) from exc
    directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "日志"
    if configure_logging:
        configure_file_logging(directory)
    return directory
