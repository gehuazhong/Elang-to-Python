"""使用真实三十二兆字节边界检查中文项目保存；所有项目均在临时目录。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from core.commands.nodes import create_node, set_property
from core.errors import DesignerError
from core.models import new_project
from core.storage import MAX_PROJECT_BYTES, atomic_write, commit_project, load_project
from widgets.builtin import create_registry


def main() -> int:
    started = perf_counter()
    report: dict[str, object] = {"容量上限字节": MAX_PROJECT_BYTES, "通过": False}
    try:
        registry = create_registry()
        project = new_project("实际容量边界检查")
        for index in range(111):
            project, key = create_node(project, registry, "builtin.label", index % 10 * 80, index // 10 * 40)
            project = set_property(project, registry, key, "text", "文" * 100_000)
        registry.validate(project)
        report["可保存项目字节"] = len(project.to_bytes())
        assert report["可保存项目字节"] <= MAX_PROJECT_BYTES
        oversized, key = create_node(project, registry, "builtin.label", 0, 480)
        oversized = set_property(oversized, registry, key, "text", "字" * 100_000)
        registry.validate(oversized)
        report["超限项目字节"] = len(oversized.to_bytes())
        assert report["超限项目字节"] > MAX_PROJECT_BYTES
        with TemporaryDirectory(prefix="uiplay-capacity-") as temporary:
            path = Path(temporary) / "中文大项目.uipro"
            token = commit_project(path, project, expected_token=None)
            assert load_project(path).model == project
            report["大项目保存加载"] = "通过"
            token = commit_project(path, project, expected_token=token)
            backup = path.with_suffix(".uipro.bak")
            previous, previous_backup = path.read_bytes(), backup.read_bytes()
            try:
                commit_project(path, oversized, expected_token=token)
            except DesignerError as error:
                assert "超过" in str(error)
                report["超限保存提示"] = str(error)
            else:
                raise AssertionError("超限项目没有被拒绝。")
            assert path.read_bytes() == previous and backup.read_bytes() == previous_backup
            report["原文件与已有备份保持"] = "通过"
            external = path.parent / "外部超限文件.uipro"
            atomic_write(external, oversized.to_bytes())
            try:
                load_project(external)
            except DesignerError as error:
                assert "超过" in str(error)
                report["超限加载提示"] = str(error)
            else:
                raise AssertionError("外部超限项目没有被拒绝。")
        report["通过"] = True
    except Exception:
        logging.getLogger(__name__).exception("实际项目容量检查失败。")
        report["通过"] = False
    finally:
        report["持续秒数"] = round(perf_counter() - started, 3)
        destination = Path(__file__).resolve().parents[1] / "reports" / "实际容量边界检查_0.7.4.json"
        atomic_write(destination, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
