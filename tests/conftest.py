"""共享离屏 Qt 环境，无需额外测试插件。"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from core.models import ProjectModel, new_project
from core.registry import WidgetRegistry
from widgets.builtin import create_registry


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    application = QApplication.instance() or QApplication([])
    application.setStyle("Fusion")
    return application


@pytest.fixture
def registry() -> WidgetRegistry:
    return create_registry()


@pytest.fixture
def project() -> ProjectModel:
    return new_project("测试窗口")
