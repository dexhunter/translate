"""Shared baseline reduction for the intake harnesses."""

from __future__ import annotations

import os


def pin_cpu() -> None:
    """Pin this process to one CPU so the spread reflects the function."""
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {0})


def median(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def full_spread_pct(values: list[float]) -> float:
    """Full spread of the samples as a percent of the median."""
    mid = median(values)
    if mid == 0:
        return 0.0
    return (max(values) - min(values)) / mid * 100.0
