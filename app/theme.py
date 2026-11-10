"""Compatibility exports for the single designer-shell theme."""

from PySide6.QtGui import QPalette

from .designer_theme import DESIGNER_QSS, designer_palette

SHELL_STYLE = DESIGNER_QSS


def shell_palette(base: QPalette) -> QPalette:
    return designer_palette(base)
