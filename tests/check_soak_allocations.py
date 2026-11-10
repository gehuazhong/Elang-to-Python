"""区分持续编辑中的 Python 保留分配与进程私有内存，作为泄漏定位证据。"""

from __future__ import annotations

import argparse
from collections import Counter
import gc
import json
from pathlib import Path
import random
import tracemalloc

from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from architecture_checks.qt_probe import private_memory
from core.storage import atomic_write
from tests.soak_designer import run_cycle, sample
from widgets.builtin import create_registry


def tracked_types() -> Counter[str]:
    return Counter(type(item).__module__ + "." + type(item).__qualname__ for item in gc.get_objects())


def main() -> None:
    parser = argparse.ArgumentParser(description="持续编辑的内存分配定位")
    parser.add_argument("--cycles", type=int, default=15, help="预热之后的检查轮次")
    args = parser.parse_args()
    application = QApplication([])
    initialize(application, configure_logging=False)
    application.setQuitOnLastWindowClosed(False)
    registry = create_registry()
    baseline = sample(registry)
    rng = random.Random(20261107)
    counters: Counter[str] = Counter()
    covered: set[str] = set()
    for cycle in range(3):
        run_cycle(application, registry, baseline, rng, cycle, counters, covered)
        gc.collect()
    tracemalloc.start(1)
    before = tracemalloc.take_snapshot()
    types_before = tracked_types()
    readings: list[dict[str, int | None]] = []
    for cycle in range(args.cycles):
        run_cycle(application, registry, baseline, rng, cycle + 3, counters, covered)
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        readings.append({"轮次": cycle + 1, "私有内存": private_memory(), "Python保留分配": current,
                         "Python分配峰值": peak, "顶层窗口": len(application.topLevelWidgets())})
        if (cycle + 1) % 5 == 0:
            print(json.dumps(readings[-1], ensure_ascii=False), flush=True)
    after = tracemalloc.take_snapshot()
    types_after = tracked_types()
    differences = [{"位置": str(stat.traceback), "增加字节": stat.size_diff, "增加分配数": stat.count_diff}
                   for stat in after.compare_to(before, "lineno")[:30]]
    growth = {key: types_after[key] - types_before[key] for key in types_after
              if types_after[key] > types_before[key] and (key.startswith("PySide6.")
                                                         or key.split(".")[0] in {"app", "core", "panels", "designer", "runtime"})}
    report = {"说明": "三轮预热后启用 Python 分配追踪；追踪器本身占用额外内存，不与无追踪基准直接比较。",
              "轮次": args.cycles, "采样": readings, "保留分配增量": differences, "受跟踪对象数量增长": growth}
    tracemalloc.stop()
    destination = Path(__file__).resolve().parents[1] / "reports" / "持续编辑分配定位_0.7.4.json"
    atomic_write(destination, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"受跟踪对象数量增长": growth, "主要保留分配": differences[:10]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
