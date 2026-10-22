"""Scoring: per-run checks, suite aggregation, reports."""

from .checks import CHECK_NAMES, score_run
from .suite import (
    RUNS,
    headline_rows,
    pass_at_k,
    pass_hat_k,
    render_html,
    render_markdown,
    run_all,
    run_suite,
)

__all__ = [
    "CHECK_NAMES",
    "score_run",
    "RUNS",
    "headline_rows",
    "pass_at_k",
    "pass_hat_k",
    "render_html",
    "render_markdown",
    "run_all",
    "run_suite",
]
