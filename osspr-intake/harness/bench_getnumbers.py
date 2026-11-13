"""
Time decoration.getnumbers on the strings a pofilter numbers check sees.

The batch is UI text: counts, versions, a doubled dot in a range, and a few
temperatures. pofilter calls getnumbers on the source and the translation.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.filters.decoration import getnumbers  # ruff: ignore[module-import-not-at-top-of-file]

RUNS = 7
WARMUP = 2
REPEATS = 6


def _batch() -> list[str]:
    rows: list[str] = []
    for i in range(12000):
        if i % 19 == 0:
            rows.append(f"Temperature is 20°C in room {i}.")
        elif i % 6 == 0:
            rows.append(f"See section {i}.2 and range 10..20.")
        elif i % 11 == 0:
            rows.append("No digits in this label at all.")
        else:
            rows.append(f"Open document {i} of 12. Item {i} has 3 parts.")
    return rows


def _run(rows: list[str]) -> int:
    total = 0
    for _ in range(REPEATS):
        for row in rows:
            total += len(getnumbers(row))
    return total


def main() -> None:
    pin_cpu()
    rows = _batch()
    assert getnumbers("Nine 9 nine") == ["9"]
    assert getnumbers("R5.99") == ["5.99"]
    assert getnumbers("36°") == ["36°"]
    assert getnumbers("a 10..20 b") == ["10..20"]
    assert getnumbers("1.") == ["1"]
    assert getnumbers(".5") == ["5"]
    assert getnumbers("English 123, Bengali \u09e7\u09e8\u09e9") == [
        "123",
        "\u09e7\u09e8\u09e9",
    ]

    for _ in range(WARMUP):
        _run(rows)
    samples: list[float] = []
    checksum = 0
    for _ in range(RUNS):
        start = time.perf_counter()
        checksum = _run(rows)
        samples.append((time.perf_counter() - start) * 1000.0)
    mid = median(samples)
    print(  # ruff: ignore[print]
        f"median_ms={mid:.4f} noise_pct={full_spread_pct(samples):.4f} "
        f"checksum={checksum} runs={','.join(f'{sample:.4f}' for sample in samples)}"
    )


if __name__ == "__main__":
    main()
