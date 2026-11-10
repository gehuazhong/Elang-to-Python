"""独立契约实验的样例和离屏应用夹具。"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from architecture_checks.contracts import Project


@pytest.fixture
def project() -> Project:
    source = Path(__file__).resolve().parents[2] / "examples" / "中文界面示例.uipro"
    return json.loads(source.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def qt_app() -> Iterator[QApplication]:
    app = QApplication.instance() or QApplication(["架构验证", "-platform", "offscreen"])
    yield app
    app.closeAllWindows()
    app.processEvents()
