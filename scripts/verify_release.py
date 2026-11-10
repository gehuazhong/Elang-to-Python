"""校验并解压便携包，在仓库外且不含 Python 搜索路径的环境中运行。"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import zipfile


class ChineseParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, "参数无效，请提供便携包路径和可选的 --report 报告路径。\n")


def verify(archive_path: Path, report: Path) -> None:
    archive_path, report = archive_path.resolve(), report.resolve()
    sidecar = archive_path.with_suffix(".sha256.txt")
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != sidecar.read_text(encoding="utf-8").split()[0]:
        raise RuntimeError("便携包摘要与随包校验文件不一致。")
    with tempfile.TemporaryDirectory(prefix="中文便携包复验_") as temporary:
        directory = Path(temporary).resolve()
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len(entries) > 20000 or sum(item.file_size for item in entries) > 2 * 1024 ** 3:
                raise RuntimeError("压缩包超过当前检查范围。")
            for entry in entries:
                relative = PurePosixPath(entry.filename)
                target = directory.joinpath(*relative.parts).resolve()
                if (not relative.parts or relative.parts[0] != "中文界面设计器" or relative.is_absolute()
                        or ".." in relative.parts or ":" in entry.filename or "\\" in entry.filename
                        or not target.is_relative_to(directory) or stat.S_ISLNK(entry.external_attr >> 16)):
                    raise RuntimeError("压缩包包含不允许的路径或符号链接。")
            if archive.testzip() is not None:
                raise RuntimeError("压缩包内容损坏。")
            archive.extractall(directory)
        bundle = directory / "中文界面设计器"
        inventory = json.loads((bundle / "构建清单.json").read_text(encoding="utf-8"))
        manifest = json.loads((bundle / "文件校验.json").read_text(encoding="utf-8"))
        for name, expected in manifest.items():
            target = (bundle / name).resolve()
            if not target.is_relative_to(bundle) or not target.is_file():
                raise RuntimeError("文件校验清单引用了无效路径。")
            if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                raise RuntimeError("解压文件的摘要不一致。")
        environment = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "QT_QPA_PLATFORM", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"):
            environment.pop(key, None)
        windows = Path(os.environ["SystemRoot"])
        environment["PATH"] = os.pathsep.join((str(windows / "System32"), str(windows)))
        working = directory / "独立工作目录"
        working.mkdir()
        subprocess.run([str(bundle / "中文界面设计器.exe"), "--release-check", str(report)],
                       cwd=working, env=environment, check=True, timeout=120)
        result = json.loads(report.read_text(encoding="utf-8"))
        if result.get("检查结果") != "通过" or not result.get("便携包"):
            raise RuntimeError("解压后的便携包未通过检查。")
        result["压缩包与逐文件摘要"] = "通过"
        result["仓库外解压运行"] = "通过"
        result["环境搜索路径"] = "仅保留 Windows 系统目录"
        if "核心源码摘要" in inventory:
            result["核心源码摘要"] = inventory["核心源码摘要"]
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = ChineseParser(add_help=False, usage="python scripts/verify_release.py 便携包路径 [--report 报告路径]")
    parser.add_argument("archive", type=Path, metavar="便携包路径")
    parser.add_argument("--report", type=Path, metavar="报告路径", default=Path("reports/便携包复验.json"))
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        verify(arguments.archive, arguments.report)
        logging.info("便携包解压、文件校验和仓库外独立运行全部通过。报告：%s", arguments.report.resolve())
        return 0
    except Exception:
        logging.getLogger(__name__).exception("便携包复验失败。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
