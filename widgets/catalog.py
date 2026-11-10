"""受支持的 Qt 类名称；代码生成读取目录时无需导入运行画布。"""

QT_WIDGET_CLASSES = frozenset({
    "QWidget", "QMainWindow", "QPushButton", "QLabel", "QLineEdit", "QPlainTextEdit", "QComboBox",
    "QCheckBox", "QRadioButton", "QSpinBox", "QProgressBar", "QSlider", "QListWidget", "QTableWidget", "QTreeWidget",
    "QGroupBox", "QFrame", "QDoubleSpinBox", "QDateEdit", "QTimeEdit", "QDateTimeEdit", "QCalendarWidget",
    "QToolButton", "QCommandLinkButton", "QDial", "QScrollBar", "QLCDNumber", "QToolBar", "QStatusBar", "QMenuBar",
    "QTextEdit", "QTextBrowser", "QFontComboBox", "QKeySequenceEdit",
})

ADAPTER_CLASSES = frozenset({"DrawingBoard", "PictureBox", "SelectionTabs", "SuperList", "CommonDialog"})
from .advanced import ADVANCED_TYPES
ADVANCED_CLASSES = frozenset(ADVANCED_TYPES.values())
COMPONENT_CLASSES = QT_WIDGET_CLASSES | ADAPTER_CLASSES | ADVANCED_CLASSES | {"QTimer", "QAction"}
SUPPORTED_SLOTS = frozenset({"root", "central", "children", "pages", "non_visual", "tool_bar", "status_bar", "menu_bar", "menu", "dock"})
