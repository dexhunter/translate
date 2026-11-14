"""
Time TranslationUnit.validate_id on resource ids a catalog assigns.

The batch is dotted UI ids, a few with the tab and newline characters the
check allows, and non-Latin keys. Invalid controls are checked separately
and are not part of the timed loop.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_REPO = _HARNESS.parents[2]
sys.path[:0] = [str(_REPO), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.storage.base import TranslationUnit  # ruff: ignore[module-import-not-at-top-of-file]

RUNS = 7
WARMUP = 2


def _ids() -> list[str]:
    rows: list[str] = []
    for i in range(50000):
        if i % 80 == 0:
            rows.append(f"name\twith\nwhitespace\r.{i}")
        elif i % 50 == 0:
            rows.append(f"clé.étiquette.{i}")
        elif i % 70 == 0:
            rows.append(f"メニュー.ファイル.{i}")
        else:
            rows.append(f"menu.file.open.document.{i}")
    return rows


def _run(unit: TranslationUnit, rows: list[str]) -> int:
    for value in rows:
        unit.validate_id(value)
    return len(rows)


def main() -> None:
    pin_cpu()
    unit = TranslationUnit()
    rows = _ids()
    unit.validate_id("name\twith\nwhitespace\r")
    unit.validate_id("鍵")
    for value in ("name\x00", "name\x1f", "name\ufffe", "name\uffff"):
        try:
            unit.validate_id(value)
        except ValueError:
            continue
        raise AssertionError(value)

    for _ in range(WARMUP):
        _run(unit, rows)
    samples: list[float] = []
    checksum = 0
    for _ in range(RUNS):
        start = time.perf_counter()
        checksum = _run(unit, rows)
        samples.append((time.perf_counter() - start) * 1000.0)
    mid = median(samples)
    print(  # ruff: ignore[print]
        f"median_ms={mid:.4f} noise_pct={full_spread_pct(samples):.4f} "
        f"checksum={checksum} runs={','.join(f'{sample:.4f}' for sample in samples)}"
    )


if __name__ == "__main__":
    main()
