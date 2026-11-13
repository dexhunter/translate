"""
Time Dialect.find_delimiter on a large Java properties file.

propfile.parse calls this once per entry. The lines are the usual mix:
'key = value', a colon delimiter, a whitespace delimiter, and a few escapes.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.storage.properties import DialectJava, DialectStrings  # ruff: ignore[module-import-not-at-top-of-file]

RUNS = 7
WARMUP = 2


def _lines() -> list[tuple[type, str]]:
    rows: list[tuple[type, str]] = []
    for i in range(50000):
        if i % 30 == 0:
            rows.append(
                (DialectJava, f"my key {i} = value {i} with spaces and a:colon")
            )
        elif i % 17 == 0:
            rows.append((DialectJava, f"app.window.action.{i}: Open document {i}"))
        elif i % 45 == 0:
            rows.append((DialectJava, f"key\\=name.{i} = value {i}"))
        elif i % 80 == 0:
            rows.append((DialectStrings, f'"menu.item.{i}" = "Open document {i}";'))
        else:
            rows.append(
                (
                    DialectJava,
                    (
                        f"app.window.action.open.{i} = "
                        f"Open document {i} and save your changes before you continue."
                    ),
                )
            )
    return rows


def _run(rows: list[tuple[type, str]]) -> int:
    total = 0
    for dialect, line in rows:
        _delimiter, pos = dialect.find_delimiter(line)
        total += pos
    return total


def main() -> None:
    pin_cpu()
    rows = _lines()
    assert DialectJava.find_delimiter("key=value") == ("=", 3)
    assert DialectJava.find_delimiter("key = value") == ("=", 4)
    assert DialectJava.find_delimiter("key:value") == (":", 3)
    assert DialectJava.find_delimiter("key value=value") == (" ", 3)
    assert DialectJava.find_delimiter("key\\:=value") == ("=", 5)
    assert DialectStrings.find_delimiter('"ke=y" = "value";') == ("=", 7)

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
