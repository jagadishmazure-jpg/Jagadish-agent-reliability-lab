"""Task suites and the runner that executes them."""

from .definitions import ALL_TASKS, SUITES
from .runner import run_task

__all__ = ["ALL_TASKS", "SUITES", "run_task"]
