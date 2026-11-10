"""仅用于验证生产保存路径在真实进程中断后的完整性。"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from core.storage import FileLease, commit_project, digest, load_project


def main() -> None:
    path, stage = Path(sys.argv[1]), sys.argv[2]
    loaded = load_project(path)
    source = path.parent / "新资源来源"
    content = b"new-resource"
    checksum = digest(content)
    relative = f"assets/{checksum}.bin"
    resource = source / relative
    resource.parent.mkdir(parents=True, exist_ok=True)
    resource.write_bytes(content)
    model = replace(loaded.model, data=loaded.model.data.changed(name="新版本", resources=[{
        "id": str(uuid4()), "name": "新资源", "kind": "binary", "path": relative, "sha256": checksum,
    }]))
    lease = FileLease(path)
    if not lease.acquired:
        raise RuntimeError("测试子进程未能取得写锁。")

    def interrupt(checkpoint: str) -> None:
        if checkpoint == stage:
            os._exit(86)

    commit_project(path, model, expected_token=loaded.token, resource_source=source, checkpoint=interrupt)


if __name__ == "__main__":
    main()
