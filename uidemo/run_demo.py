"""运行或在当前设计器中打开一个示例。"""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    base = Path(__file__).resolve().parent
    examples = {
        "1": ("01_库存管理台", "库存管理台"),
        "2": ("02_任务下载中心", "任务下载中心"),
        "3": ("03_账号登录", "账号登录"),
        "4": ("04_应用设置", "应用设置"),
        "5": ("05_菜单编辑示例", "菜单编辑示例"),
        "6": ("06_文本与输入组件", "文本与输入组件"),
        "7": ("07_兔子工具个人中心", "兔子工具个人中心"),
    }
    parser = argparse.ArgumentParser(description="1 库存管理台；2 任务下载中心；3 账号登录；4 应用设置；5 菜单编辑示例；6 文本与输入组件；7 兔子工具个人中心。")
    parser.add_argument("example", choices=examples, nargs="?", default="1", help="示例编号，默认 1")
    parser.add_argument("--edit", action="store_true", help="用当前项目的设计器打开设计文件")
    args = parser.parse_args()
    directory, name = examples[args.example]
    folder = base / directory
    if args.edit:
        command = [sys.executable, "-X", "utf8", str(base.parent / "main.py"), str(folder / (name + ".uipro"))]
    else:
        command = [sys.executable, "-X", "utf8", str(folder / "Python导出" / "main.py")]
    return subprocess.call(command, cwd=folder)


if __name__ == "__main__":
    raise SystemExit(main())

