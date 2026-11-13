"""
Time StandardChecker.pythonbraceformat on a pofilter-sized PO batch.

Most pairs are plain UI text. About one eighth use Python brace placeholders,
which is the mix the check sees in a real file.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.filters.checks import StandardChecker  # ruff: ignore[module-import-not-at-top-of-file]
from translate.filters.checks.exceptions import (  # ruff: ignore[module-import-not-at-top-of-file]
    FilterFailure,
    SeriousFilterFailure,
)

RUNS = 7
WARMUP = 2


def _pairs() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for i in range(16000):
        if i % 8 == 0:
            source = "Hello {name}, you have {count} messages."
            if i % 16 == 0:
                target = "Bonjour {user}, vous avez {count} messages."
            else:
                target = "Bonjour {name}, vous avez {count} messages."
        else:
            source = f"Open document {i} and save your changes."
            target = f"Ouvrir le document {i} et enregistrer."
        rows.append((source, target))
    return rows


def _run(checker: StandardChecker, rows: list[tuple[str, str]]) -> int:
    failures = 0
    for source, target in rows:
        try:
            checker.pythonbraceformat(source, target)
        except FilterFailure:
            failures += 1
        except SeriousFilterFailure:
            failures += 3
    return failures


def main() -> None:
    pin_cpu()
    checker = StandardChecker()
    rows = _pairs()
    assert checker.pythonbraceformat("Open the file.", "Ouvrir le fichier.") == 1
    assert checker.pythonbraceformat("Hello {name}", "Bonjour {name}") == 1
    try:
        checker.pythonbraceformat("String {}", "String {} en nommer {}")
    except FilterFailure:
        pass
    else:
        raise AssertionError("expected a mild brace failure")

    for _ in range(WARMUP):
        _run(checker, rows)
    samples: list[float] = []
    checksum = 0
    for _ in range(RUNS):
        start = time.perf_counter()
        checksum = _run(checker, rows)
        samples.append((time.perf_counter() - start) * 1000.0)
    mid = median(samples)
    print(  # ruff: ignore[print]
        f"median_ms={mid:.4f} noise_pct={full_spread_pct(samples):.4f} "
        f"checksum={checksum} runs={','.join(f'{sample:.4f}' for sample in samples)}"
    )


if __name__ == "__main__":
    main()
