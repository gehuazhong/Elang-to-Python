"""串行验证桌面交互，避免多个测试窗口争夺焦点。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic
from typing import Any


CHECKS = (
    "check_desktop", "check_workbench", "check_audit", "check_interactions", "check_multiselect",
    "check_clipboard", "check_line_edit", "check_standard_widgets", "check_extended_widgets",
    "check_easy_widgets", "check_canvas_view", "check_font_editor", "check_window_scaling",
    "check_property_interactions", "check_preview",
    "check_screen_fit", "check_window_icon",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="串行执行桌面验收并汇总结果")
    parser.add_argument("--scale", choices=("1", "1.5", "2"), default="1", help="界面缩放倍率")
    args = parser.parse_args()
    base = Path(__file__).resolve().parents[1]
    environment = dict(os.environ, QT_SCALE_FACTOR=args.scale, PYTHONIOENCODING="utf-8")
    environment.pop("QT_QPA_PLATFORM", None)
    results: list[dict[str, Any]] = []
    for check in CHECKS:
        started = monotonic()
        try:
            result = subprocess.run([sys.executable, "-X", "utf8", "-m", "tests." + check], cwd=base,
                                    env=environment, capture_output=True, text=True, encoding="utf-8", timeout=60)
            record = {"检查": check, "通过": result.returncode == 0, "退出码": result.returncode,
                      "耗时秒": round(monotonic() - started, 3), "输出": result.stdout[-8000:], "错误输出": result.stderr[-8000:]}
        except (OSError, subprocess.TimeoutExpired) as exc:
            record = {"检查": check, "通过": False, "异常": str(exc)}
        results.append(record)
        print(f"{check}：{'通过' if record['通过'] else '失败'}", flush=True)
    target = base / "reports" / f"稳定性桌面验收_{round(float(args.scale) * 100)}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"缩放倍率": args.scale, "通过": all(item["通过"] for item in results),
                                  "检查": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(item["通过"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
