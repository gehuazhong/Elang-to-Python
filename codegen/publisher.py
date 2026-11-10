"""先准备完整版本，再原子切换指针，绝不覆盖用户业务文件。"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
from pathlib import Path
import tempfile
from typing import Callable

from core.errors import DesignerError, require
from core.events import event_bindings
from core.models import ProjectModel
from core.registry import WidgetRegistry
from core.storage import FileLease, atomic_write, no_fault
from .generator import generate_files

logger = logging.getLogger(__name__)
HANDLERS = '''"""业务代码由您维护，后续导出不会覆盖此文件。"""

from PySide6.QtWidgets import QMainWindow


def connect_events(window: QMainWindow) -> None:
    """在此连接信号；通过 window.controls[代码名称] 获取控件。"""
    # 例如：window.controls["button_1"].clicked.connect(lambda: window.setWindowTitle("按钮已单击"))
    return None
'''
INSTRUCTIONS = '''# 独立界面项目

此目录包含完整界面源代码，只需要 Python 3.11 或以上版本和 PySide6。

在此目录打开终端，执行：

```powershell
python -m pip install -r requirements.txt
python main.py
```

在设计器中勾选事件后，导出会自动连接，并在 event_handlers 目录为每个处理函数生成一个 Python 文件。
将业务代码写入对应函数；第一个参数 window 是窗口，其余 arguments 是原始 Qt 信号参数。
鼠标、键盘、关闭等通用事件的 arguments[0] 是 Qt 事件对象，只在本次调用中使用；返回 True 可阻止默认处理。
例如，关闭事件中调用 arguments[0].ignore() 并返回 True 可取消关闭；拖放需在拖动进入事件中调用 acceptProposedAction() 并返回 True。
未勾选的事件不自动连接。取消勾选不会删除处理函数文件；重新勾选继续使用原有代码。
预览只报告勾选事件的触发，不执行导出目录中的业务代码。
handlers.py 的 connect_events 函数仍可用于窗口初始化或手动连接。在其中通过 window.controls["代码名称"] 获取控件。
控件代码名称可在设计器“属性 → 高级 → 代码名称”中选中复制，或查看 generated 当前版本的 ui_main.py。
例如，默认按钮可用 window.controls["button_1"].clicked.connect(...) 连接被单击事件。

时钟使用 timeout 信号，周期单位为毫秒，可调用 start() 和 stop()。自动启动在窗口创建完成后进行。
通用对话框可通过设计时选定的按钮触发，也可调用 open_dialog()；accepted 返回文件路径列表、颜色文本或字体字典。
画板支持 draw_line(x1, y1, x2, y2) 和 clear()；运行时绘画不会回写设计项目。
选择夹可调用 set_current_page(页号)，页号从零开始；超级列表框使用原生 itemClicked、itemDoubleClicked 和 itemChanged 信号。
表格和超级列表框会保留设计时设置的各列宽度；明确设置宽度的末列不会自动拉伸。运行时可调用 setColumnWidth(列号, 宽度) 调整，列号从零开始。
工具条使用 actionTriggered 信号，参数为被触发的动作；状态条可调用 showMessage(文本)。
图片已导出到当前生成版本的 assets 子目录，请连同生成目录一起保留。
窗口的“程序图标”也随 assets 导出，运行时从相对路径加载，无需保留导入时的原文件。此属性设置运行窗口的图标；可执行文件的文件图标由打包配置决定。
设计器窗口属性中的“组件随窗口缩放”开启后，导出窗口会按比例调整组件位置和大小；字体字号、工具条和状态条高度保持设计值。运行时以设计基准计算，不回写设计项目。

更新界面时，重新导出到本目录。入口 main.py、handlers.py 和 event_handlers 中已有文件不会被覆盖；新界面在生成完整后才发布。
请保留 connect_events 函数，接收一个窗口参数，不添加装饰器；可以从同目录导入自己的业务模块。
请勿手工修改 current.json 或 generated 内的文件。旧界面版本会保留，不会自动清理。
如果修改了入口或自动生成文件，请先备份改动，再选择新目录导出。

代码导出不会代替 .uipro 设计项目保存。请备份设计项目以及此完整目录。
业务文件仅进行语法和入口签名检查；其中的业务行为需要自行运行验证。
'''


def event_sources(model: ProjectModel, registry: WidgetRegistry) -> dict[str, bytes]:
    sources = {}
    for binding in event_bindings(model, registry):
        name = binding.get("handler")
        if name is None:
            continue
        description = f"处理{binding['name']}的{binding['label']}事件；后续导出不会覆盖此文件。"
        source = (repr(description) + f"\n\n\ndef {name}(window, *arguments):\n"
                  '    """通过 window.controls 访问组件；arguments 接收原始信号参数或事件对象。"""\n'
                  "    return None\n")
        sources[name + ".py"] = source.encode("utf-8")
    return sources


def validate_event_source(content: bytes, name: str) -> None:
    try:
        tree = ast.parse(content.decode("utf-8-sig"))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
        require(len(functions) == 1 and not functions[0].decorator_list,
                f"事件文件需要保留一个未加装饰器的 {name} 函数。")
        arguments = functions[0].args
        require(bool(arguments.posonlyargs + arguments.args) and
                all(default is not None for default in arguments.kw_defaults),
                f"事件函数 {name} 需要接收窗口及事件参数，不能含必填关键字参数。")
    except (SyntaxError, UnicodeError) as exc:
        raise DesignerError(f"事件函数 {name} 存在语法或编码错误，已保留当前导出版本。") from exc


def export_project(model: ProjectModel, registry: WidgetRegistry, target: Path,
                   *, checkpoint: Callable[[str], None] = no_fault) -> Path:
    files = generate_files(model, registry)
    sources = event_sources(model, registry)
    launcher = Path(__file__).with_name("launcher.py").read_bytes()
    identity = hashlib.sha256()
    for name, content in sorted(files.items()):
        identity.update(name.encode("utf-8") + b"\0" + content + b"\0")
    version = identity.hexdigest()
    try:
        target = target.expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DesignerError("无法建立导出目录，请检查目录权限和磁盘空间。") from exc
    require(not (target / "current.json").is_symlink()
            and (target / "current.json").resolve().is_relative_to(target), "导出版本指针不能是外部链接。")
    lease = FileLease(target / "current.json")
    require(lease.acquired, "导出目录正在使用，请稍后重试。")
    try:
        entry, handlers, pointer = target / "main.py", target / "handlers.py", target / "current.json"
        marker = target / ".uiplay-export.json"
        event_directory = target / "event_handlers"
        for path in (entry, handlers, pointer, target / "generated", marker, event_directory):
            require(not path.is_symlink() and path.resolve().is_relative_to(target), "导出目录中的受管理路径不能是符号链接或外部目录联接。")
        if entry.exists():
            require(entry.read_bytes() == launcher, "导出入口已有其他内容或版本不兼容，请选择新目录。")
        if pointer.exists():
            old = json.loads(pointer.read_text(encoding="utf-8"))
            require(isinstance(old, dict) and old.get("protocol") == 1 and old.get("document_id") == model.data["document_id"],
                    "该目录属于其他项目或导出协议，请选择新目录。")
            require(handlers.is_file(), "既有导出的业务文件缺失，请恢复 handlers.py 或选择新目录。")
        elif marker.exists():
            owner = json.loads(marker.read_text(encoding="utf-8"))
            require(isinstance(owner, dict) and owner.get("protocol") == 1
                    and owner.get("document_id") == model.data["document_id"], "未完成的导出属于其他项目。")
        else:
            require(not handlers.exists() and not (target / "generated").exists() and not event_directory.exists(),
                    "目标目录包含未完成或非本项目的导出，请选择新目录。")
        business_before = handlers.read_bytes() if handlers.exists() else None
        event_before = {}
        for name, content in sources.items():
            path = event_directory / name
            require(not path.is_symlink() and path.resolve().is_relative_to(target),
                    "事件处理函数文件不能是符号链接或外部目录联接。")
            event_before[name] = path.read_bytes() if path.exists() else None
            validate_event_source(event_before[name] if event_before[name] is not None else content, Path(name).stem)
        if handlers.exists():
            try:
                business_ast = ast.parse(business_before.decode("utf-8-sig"))
                functions = [node for node in business_ast.body if isinstance(node, ast.FunctionDef)
                             and node.name == "connect_events"]
                require(len(functions) == 1 and not functions[0].decorator_list,
                        "业务文件需要保留一个未加装饰器的 connect_events 函数。")
                arguments = functions[0].args
                require(len(arguments.posonlyargs + arguments.args) == 1 and not arguments.vararg
                        and not arguments.kwarg and not arguments.kwonlyargs,
                        "业务入口 connect_events 需要接收一个窗口参数。")
            except (SyntaxError, UnicodeError) as exc:
                raise DesignerError("业务文件存在语法或编码错误，已保留当前导出版本。") from exc
        if not pointer.exists() and not marker.exists():
            atomic_write(marker, json.dumps({"protocol": 1, "document_id": model.data["document_id"]}).encode("utf-8"))
        versions = target / "generated"
        versions.mkdir(exist_ok=True)
        destination = versions / version
        require(not destination.is_symlink() and destination.resolve().is_relative_to(versions),
                "生成版本目录不能是符号链接或外部目录联接。")
        if destination.exists():
            require(all((destination / name).is_file() and not (destination / name).is_symlink()
                        and (destination / name).read_bytes() == content for name, content in files.items()),
                    "已有生成文件被修改，请保留修改并选择新目录导出。")
        else:
            with tempfile.TemporaryDirectory(prefix=".准备_", dir=versions) as temporary:
                staged = Path(temporary) / version
                staged.mkdir()
                for name, content in files.items():
                    (staged / name).parent.mkdir(parents=True, exist_ok=True)
                    atomic_write(staged / name, content)
                checkpoint("version.ready")
                staged.rename(destination)
        for path, content in ((entry, launcher), (handlers, HANDLERS.encode("utf-8")),
                              (target / "requirements.txt", b"PySide6==6.11.1\n"),
                              (target / "使用说明.md", INSTRUCTIONS.encode("utf-8"))):
            if not path.exists():
                with path.open("xb") as stream:
                    stream.write(content)
        if sources:
            event_directory.mkdir(exist_ok=True)
            for name, content in sources.items():
                if event_before[name] is None:
                    with (event_directory / name).open("xb") as stream:
                        stream.write(content)
        checkpoint("before.publish")
        require(handlers.read_bytes() == (business_before if business_before is not None else HANDLERS.encode("utf-8")),
                "导出期间业务文件发生了变化，请再次导出。")
        require(all((event_directory / name).read_bytes() ==
                    (event_before[name] if event_before[name] is not None else content)
                    for name, content in sources.items()), "导出期间事件处理函数发生了变化，请再次导出。")
        payload = json.dumps({"protocol": 1, "document_id": model.data["document_id"], "version": version},
                             ensure_ascii=False, indent=2).encode("utf-8")
        atomic_write(pointer, payload)
        return entry
    except DesignerError:
        raise
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        logger.exception("代码导出未完成。")
        raise DesignerError("代码导出失败，请检查目录权限、磁盘空间与已有文件。") from exc
    finally:
        lease.release()
