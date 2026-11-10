"""在独立测试进程中强制退出，验证操作系统实际提交边界。"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from .contracts import Project
from .storage_probe import commit_project, digest, file_token, publish_generation


def main() -> int:
    if len(sys.argv) != 4:
        print("用法：验证模块 项目或导出 目标路径 检查点")
        return 2
    kind, destination, target_stage = sys.argv[1:]
    path = Path(destination)

    def interrupt(stage: str) -> None:
        if stage == target_stage:
            os._exit(86)

    try:
        if kind == "project":
            project: Project = json.loads(path.read_text(encoding="utf-8"))
            project["name"] = "修改后"
            payload = "新的资源内容".encode("utf-8")
            checksum = digest(payload)
            resource_id = "5c47e92a-75a8-4e78-b8ed-1dd1ba6186fe"
            project["resources"] = [{
                "id": resource_id, "name": "新资源", "kind": "binary",
                "path": f"assets/{checksum}.bin", "sha256": checksum,
            }]
            commit_project(path, project, {resource_id: payload},
                           expected_token=file_token(path), checkpoint=interrupt)
        elif kind == "export":
            publish_generation(path, {"ui_main.py": b"new-ui", "assets/value.bin": b"new-resource"},
                               expected_token=file_token(path / "current.json"), checkpoint=interrupt)
        else:
            raise ValueError("验证种类不受支持。")
    except Exception:
        logging.exception("中断验证进程执行失败。")
        return 1
    print("指定检查点没有触发中断。")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
