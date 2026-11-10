"""Graphics surfaces are created lazily; the editor never starts a browser or GPU."""

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap, QSurfaceFormat
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QSplashScreen
from .easy_widgets import decoded_image
from .advanced_containers import TriggerWindow
from .property_completion import ALIGNMENTS


class GraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)

    def configure(self, values):
        scene = self.graphics_scene
        scene.clear()
        scene.setSceneRect(0, 0, values["scene_width"], values["scene_height"])
        if values["image"]:
            scene.addPixmap(QPixmap.fromImage(decoded_image(values["image"])))
        if values["text"]:
            scene.addText(values["text"])
        self.resetTransform()
        self.scale(values["zoom"] / 100, values["zoom"] / 100)
        self.setInteractive(values["interactive"])


class LazySurface(QWidget):
    label = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.design_mode = True
        self.native = None
        self.values = {}
        self.host_layout = QVBoxLayout(self)
        self.host_layout.setContentsMargins(0, 0, 0, 0)

    def configure(self, values):
        self.values = values
        self.update()

    def paintEvent(self, event):
        if self.native is None:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(self.values.get("clear_color", "#203044")))
            painter.setPen(QColor("#c6d4e1"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.label)
            painter.end()

    def dispose(self):
        if self.native is not None:
            self.native.close()
            self.native.deleteLater()
            self.native = None


class WebView(LazySurface):
    label = "网页控件\n预览时加载页面"
    loadStarted = Signal()
    loadProgress = Signal(int)
    loadFinished = Signal(bool)
    urlChanged = Signal(QUrl)
    titleChanged = Signal(str)

    def configure(self, values):
        old_source = tuple(self.values.get(key) for key in ("source_mode", "html", "url"))
        super().configure(values)
        if self.native is not None:
            self.apply_settings()
            if old_source != tuple(values.get(key) for key in ("source_mode", "html", "url")):
                self.load_source()

    def apply_settings(self):
        from PySide6.QtWebEngineCore import QWebEngineSettings
        settings = self.native.settings()
        for key, name, default in (("javascript", "JavascriptEnabled", True), ("auto_load_images", "AutoLoadImages", True),
                                  ("local_storage", "LocalStorageEnabled", True), ("pdf_viewer", "PdfViewerEnabled", True)):
            settings.setAttribute(getattr(QWebEngineSettings.WebAttribute, name), self.values.get(key, default))
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, self.values.get("default_font_size", 16))
        settings.setFontSize(QWebEngineSettings.FontSize.MinimumFontSize, self.values.get("minimum_font_size", 0))
        self.native.page().setBackgroundColor(QColor(self.values.get("page_background", "#ffffff")))
        self.native.setZoomFactor(self.values["zoom_factor"])

    def load_source(self):
        if self.values["source_mode"] == "url":
            self.native.setUrl(QUrl(self.values["url"]))
        else:
            self.native.setHtml(self.values["html"], QUrl("about:blank"))

    def start(self):
        if self.design_mode or self.native is not None:
            return
        from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
        QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)
        from PySide6.QtWebEngineWidgets import QWebEngineView
        self.native = QWebEngineView(self)
        self.host_layout.addWidget(self.native)
        for name in ("loadStarted", "loadProgress", "loadFinished", "urlChanged", "titleChanged"):
            getattr(self.native, name).connect(getattr(self, name))
        self.apply_settings()
        self.load_source()


class GpuSurface(LazySurface):
    initialized = Signal()
    rendered = Signal()
    failed = Signal(str)
    kind = "opengl"
    label = "OpenGL 绘图控件\n预览时创建图形上下文"

    def configure(self, values):
        samples_changed = self.values.get("samples") != values["samples"]
        super().configure(values)
        if self.native is not None:
            if samples_changed:
                self.dispose()
                self.start()
            else:
                self.apply_options()
                self.native.update()

    def apply_options(self):
        if self.kind == "opengl":
            from PySide6.QtOpenGLWidgets import QOpenGLWidget
            self.native.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.PartialUpdate if self.values.get("update_behavior") == "partial"
                                          else QOpenGLWidget.UpdateBehavior.NoPartialUpdate)
        else:
            self.native.setMirrorVertically(self.values.get("mirror_vertically", False))

    def start(self):
        if self.design_mode or self.native is not None:
            return
        owner = self
        try:
            if self.kind == "opengl":
                from PySide6.QtOpenGLWidgets import QOpenGLWidget

                class Surface(QOpenGLWidget):
                    def initializeGL(self):
                        owner.initialized.emit()

                    def paintGL(self):
                        color = QColor(owner.values["clear_color"])
                        functions = self.context().functions()
                        functions.glClearColor(color.redF(), color.greenF(), color.blueF(), color.alphaF())
                        functions.glClear(0x00004000 | 0x00000100)
                        owner.rendered.emit()

                self.native = Surface(self)
                fmt = QSurfaceFormat()
                fmt.setSamples(self.values["samples"])
                self.native.setFormat(fmt)
            else:
                from PySide6.QtWidgets import QRhiWidget
                from PySide6.QtGui import QRhiDepthStencilClearValue

                class Surface(QRhiWidget):
                    def initialize(self, command_buffer):
                        owner.initialized.emit()

                    def render(self, command_buffer):
                        command_buffer.beginPass(self.renderTarget(), QColor(owner.values["clear_color"]),
                                                 QRhiDepthStencilClearValue(1.0, 0))
                        command_buffer.endPass()
                        owner.rendered.emit()

                self.native = Surface(self)
                self.native.setApi(QRhiWidget.Api.OpenGL)
                self.native.setSampleCount(self.values["samples"])
                self.native.renderFailed.connect(lambda: self.failed.emit("图形上下文初始化失败"))
            self.host_layout.addWidget(self.native)
            self.apply_options()
            if self.kind == "opengl":
                QTimer.singleShot(1000, self, self._check_context)
        except (ImportError, RuntimeError) as exc:
            self.failed.emit(str(exc))

    def _check_context(self):
        if self.native is not None and not self.native.isValid():
            self.failed.emit("OpenGL 上下文初始化失败")


class RhiWidget(GpuSurface):
    kind = "rhi"
    label = "硬件渲染控件\n预览时创建 RHI 上下文"


class SvgWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtSvgWidgets import QSvgWidget
        self.native = QSvgWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.native)

    def configure(self, values):
        self.native.load(values["svg_data"].encode("utf-8"))
        self.native.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio if values.get("keep_aspect_ratio", False)
                                                 else Qt.AspectRatioMode.IgnoreAspectRatio)
        self.native.renderer().setAnimationEnabled(values.get("animation_enabled", True))


class SplashScreen(QWidget, TriggerWindow):
    messageChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.design_mode = True
        self.values = {}
        self.native = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._close_splash)

    def configure(self, values):
        self.values = values
        self.update()

    def _pixmap(self):
        image = decoded_image(self.values["image"])
        if not image.isNull():
            return QPixmap.fromImage(image)
        pixmap = QPixmap(self.size())
        pixmap.fill(QColor("#203044"))
        return pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._pixmap())
        painter.setPen(QColor(self.values.get("text_color", "#ffffff")))
        painter.drawText(self.rect(), ALIGNMENTS[self.values.get("message_alignment", "bottom_center")], self.values.get("text", ""))
        painter.end()

    def open_dialog(self, checked=False):
        if self.design_mode:
            return
        self._close_splash()
        self.native = QSplashScreen(self._pixmap())
        self.native.messageChanged.connect(self.messageChanged)
        self.native.showMessage(self.values["text"], ALIGNMENTS[self.values.get("message_alignment", "bottom_center")],
                                QColor(self.values["text_color"]))
        self.native.show()
        if self.values["duration"]:
            self.timer.start(self.values["duration"])

    def _close_splash(self):
        self.timer.stop()
        if self.native is not None:
            self.native.close()
            self.native.deleteLater()
            self.native = None

    def dispose(self):
        self.bind_trigger(None)
        self._close_splash()


GRAPHICS_FACTORIES = {"QGraphicsView": GraphicsView, "QOpenGLWidget": GpuSurface, "QRhiWidget": RhiWidget,
                      "QSvgWidget": SvgWidget, "QWebEngineView": WebView, "QSplashScreen": SplashScreen}
