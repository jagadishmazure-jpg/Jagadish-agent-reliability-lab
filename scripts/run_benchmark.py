#!/usr/bin/env python3
"""Run both agents over all three suites and write the reports.

Usage:  python3 scripts/run_benchmark.py
Prints the headline table and writes reports/benchmark.md + .html.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import NaiveAgent, ReliableAgent  # noqa: E402
from scoring import headline_rows, render_html, render_markdown, run_all  # noqa: E402


def main() -> int:
    results = run_all([NaiveAgent, ReliableAgent], runs=3)
    for row in headline_rows(results):
        b, h, d, t = row["base"], row["hallucination"], row["disambiguation"], row["total"]
        print(
            f"{row['agent']:>9}  base {b[0]}/{b[1]}  "
            f"hallucination {h[0]}/{h[1]}  disambiguation {d[0]}/{d[1]}  "
            f"total pass^3 {t[0]}/{t[1]}"
        )
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports"
    )
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "benchmark.md"), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(results))
    with open(os.path.join(out_dir, "benchmark.html"), "w", encoding="utf-8") as fh:
        fh.write(render_html(results))
    print("reports written to reports/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
