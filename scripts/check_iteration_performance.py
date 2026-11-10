"""Measure immutable model construction and plan compilation on fixed inputs."""

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from core.build_plan import compile_plan
from core.models import Rect, new_node, new_project
from scripts.source_fingerprint import source_fingerprint
from widgets.builtin import create_registry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label", choices=("before", "after"))
    args = parser.parse_args()
    registry = create_registry()
    model = new_project("Performance fixture")
    defaults = registry.require("builtin.button").defaults()
    nodes = [new_node("builtin.button", f"Button {i}", f"button_{i}", model.central_id,
                      "children", i, Rect(0, 0, 100, 30), defaults) for i in range(500)]
    model = model.with_nodes({node.id: node for node in nodes})
    for _ in range(2):
        compile_plan(model, registry, "warmup")
    timings = []
    for index in range(7):
        start = perf_counter()
        plan = compile_plan(model, registry, str(index))
        timings.append(round((perf_counter() - start) * 1000, 3))
        assert len(plan.nodes) == 502
    result = {"visual_controls": 500, "runs_ms": timings, "median_ms": median(timings),
              "registry_fingerprint": registry.fingerprint,
              "source_fingerprint": source_fingerprint(Path(__file__).resolve().parents[1])}
    output = Path(__file__).resolve().parents[1] / "reports/iteration-20261111"
    output.mkdir(parents=True, exist_ok=True)
    (output / ("performance-" + args.label + ".json")).write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
