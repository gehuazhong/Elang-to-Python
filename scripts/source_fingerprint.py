"""为稳定性检查和交付清单核对核心源码，避免混淆同版本的不同构建。"""

from __future__ import annotations

import hashlib
from pathlib import Path


def source_fingerprint(root: Path) -> str:
    checksum = hashlib.sha256()
    for folder in ("app", "core", "designer", "panels", "runtime", "layout", "preview", "codegen", "widgets"):
        for path in sorted((root / folder).rglob("*.py")):
            checksum.update(str(path.relative_to(root)).encode("utf-8"))
            checksum.update(path.read_bytes())
    for path in sorted((root / "resources").iterdir()):
        if path.is_file() and path.suffix in {".py", ".svg", ".ico", ".png"}:
            checksum.update(str(path.relative_to(root)).encode("utf-8"))
            checksum.update(path.read_bytes())
    return checksum.hexdigest()
