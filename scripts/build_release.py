"""构建独立目录包，运行实际交付检查，生成依赖清单和文件校验值。"""

from __future__ import annotations

from datetime import datetime
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.version import VERSION
from scripts.source_fingerprint import source_fingerprint


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)
    try:
        if os.name != "nt":
            raise RuntimeError("此构建脚本目前仅验证 Windows 目录式便携包。")
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        if metadata["project"]["version"] != VERSION:
            raise RuntimeError("应用版本与项目配置不一致。")
        source_hash = source_fingerprint(ROOT)
        identifier = VERSION + "-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        prepared = ROOT / "build" / identifier
        destination = ROOT / "dist" / identifier
        prepared.mkdir(parents=True, exist_ok=False)
        destination.mkdir(parents=True, exist_ok=False)
        licenses = prepared / "许可证"
        licenses.mkdir()
        dependencies = []
        for name in ("PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "PyInstaller"):
            distribution = importlib.metadata.distribution(name)
            expected = "6.19.0" if name == "PyInstaller" else "6.11.1"
            if distribution.version != expected:
                raise RuntimeError(f"{name} 版本与已验证基线不一致，需要 {expected}。")
            copied = []
            for value in distribution.files or ():
                if "licenses" in value.parts and distribution.locate_file(value).is_file():
                    output = licenses / name / value.name
                    output.parent.mkdir(exist_ok=True)
                    shutil.copy2(distribution.locate_file(value), output)
                    copied.append(str(output.relative_to(licenses)))
            dependencies.append({"名称": name, "版本": distribution.version,
                                 "分发元数据许可": distribution.metadata.get("License-Expression") or distribution.metadata.get("License"),
                                 "已收集许可": copied})
        shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", licenses / "Python许可.txt")
        upstream = ROOT / "release/licenses"
        if not upstream.is_dir() or not (upstream / "LGPL-3.0-only.txt").is_file():
            raise RuntimeError("缺少已核对的 Qt 上游许可证原文。")
        for record in json.loads((upstream / "来源.json").read_text(encoding="utf-8"))["文件"]:
            if hashlib.sha256((upstream / record["名称"]).read_bytes()).hexdigest() != record["摘要"]:
                raise RuntimeError("Qt 上游许可证原文摘要不一致。")
        shutil.copytree(upstream, licenses / "Qt上游许可")
        shutil.copy2(ROOT / "resources/app_icon.ico", prepared / "应用图标.ico")
        environment = os.environ.copy()
        environment["UIPLAY_BUILD_DATA"] = str(prepared)
        environment["PYTHONIOENCODING"] = "utf-8"
        logger.info("正在构建目录式便携包。")
        with (prepared / "构建日志.txt").open("w", encoding="utf-8") as log:
            subprocess.run([sys.executable, "-X", "utf8", "-m", "PyInstaller", "--noconfirm",
                            "--distpath", str(destination), "--workpath", str(prepared / "work"),
                            str(ROOT / "release/uiplay.spec")], cwd=ROOT, env=environment,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        bundle = destination / "中文界面设计器"
        for name in ("使用说明.txt", "第三方说明.txt"):
            shutil.copy2(ROOT / "release" / name, bundle / name)
        examples = bundle / "示例"
        examples.mkdir()
        shutil.copy2(ROOT / "examples/第二阶段示例.uipro", examples / "基础示例.uipro")
        shutil.copy2(ROOT / "examples/常用组件示例.uipro", examples / "常用组件示例.uipro")
        shutil.copy2(ROOT / "examples/容器与日期示例.uipro", examples / "容器与日期示例.uipro")
        shutil.copy2(ROOT / "examples/易语言基础组件示例.uipro", examples / "易语言基础组件示例.uipro")
        shutil.copy2(ROOT / "examples/窗口组件跟随示例.uipro", examples / "窗口组件跟随示例.uipro")
        shutil.copy2(ROOT / "uidemo/05_菜单编辑示例/菜单编辑示例.uipro", examples / "菜单编辑示例.uipro")
        shutil.copy2(ROOT / "uidemo/06_文本与输入组件/文本与输入组件.uipro", examples / "文本与输入组件.uipro")
        shutil.copy2(ROOT / "docs/组件支持矩阵.md", bundle / "组件支持矩阵.md")
        report = bundle / "交付检查.json"
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        environment.pop("QT_QPA_PLATFORM", None)
        logger.info("正在仓库外启动便携包，检查保存、加载、导出与独立预览。")
        with tempfile.TemporaryDirectory(prefix="便携包外部启动_") as working:
            subprocess.run([str(bundle / "中文界面设计器.exe"), "--release-check", str(report)],
                           cwd=working, env=environment, timeout=120, check=True)
        result = json.loads(report.read_text(encoding="utf-8"))
        if result.get("检查结果") != "通过" or not result.get("便携包"):
            raise RuntimeError("便携包未通过交付检查。")
        if source_fingerprint(ROOT) != source_hash:
            raise RuntimeError("构建期间核心源码发生变化，请重新构建以避免混合版本。")
        inventory = {"版本": VERSION, "构建时间": datetime.now().isoformat(), "解释器版本": sys.version,
                     "核心源码摘要": source_hash,
                     "依赖": dependencies, "检查结果": result,
                     "许可核对记录": "已收集分发许可和 Qt 上游许可；分发文件差异及发行待办见第三方说明。"}
        (bundle / "构建清单.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
        checksums = {path.relative_to(bundle).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(bundle.rglob("*")) if path.is_file()}
        (bundle / "文件校验.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")
        archive = destination / f"中文界面设计器-{VERSION}-开发预览.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as packed:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    packed.write(path, str(Path(bundle.name) / path.relative_to(bundle)))
        with zipfile.ZipFile(archive) as packed:
            if packed.testzip() is not None:
                raise RuntimeError("便携包压缩完整性检查失败。")
            for name, expected in checksums.items():
                if hashlib.sha256(packed.read(bundle.name + "/" + name)).hexdigest() != expected:
                    raise RuntimeError("压缩后的文件校验不一致。")
        checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
        archive.with_suffix(".sha256.txt").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
        logger.info("交付检查通过。便携包：%s", archive)
        return 0
    except Exception:
        logger.exception("构建未完成；准备目录与构建日志已保留供排查。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
