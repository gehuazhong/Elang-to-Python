# 中文界面设计器的目录式便携包；界面与预览复用一个无控制台入口。

import os
from pathlib import Path

root = Path(SPECPATH).parent
prepared = Path(os.environ["UIPLAY_BUILD_DATA"])
datas = [(str(root / name), str(Path(name).parent)) for name in (
    "runtime/appearance.py", "runtime/application.py", "runtime/widget_properties.py", "runtime/easy_widgets.py", "runtime/events.py", "runtime/menus.py", "runtime/control_features.py", "runtime/property_completion.py", "runtime/navigation.py", "codegen/launcher.py",
    "layout/__init__.py", "layout/scaling.py", "layout/runtime.py", "layout/containers.py",
    "runtime/advanced_widgets.py", "runtime/advanced_containers.py", "runtime/advanced_dialogs.py",
    "runtime/advanced_views.py", "runtime/advanced_graphics.py",
)]
datas.append((str(prepared / "许可证"), "许可证"))
datas.extend((str(path), "resources") for path in sorted((root / "resources").glob("*.svg")))
datas.append((str(root / "resources/app_icon.ico"), "resources"))

analysis = Analysis(
    [str(root / "main.py")], pathex=[str(root)], binaries=[], datas=datas,
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "pytest", "tkinter", "numpy", "matplotlib"],
    noarchive=False,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive, analysis.scripts, [], exclude_binaries=True, name="中文界面设计器",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
    icon=str(prepared / "应用图标.ico"), version=str(root / "release/version_info.txt"),
)
bundle = COLLECT(executable, analysis.binaries, analysis.datas, strip=False, upx=False,
                 name="中文界面设计器")
