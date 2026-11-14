"""
Time trados.unescape on a translation-memory export.

Most segments are plain sentences. About one in twenty uses a Trados escape
such as \\emdash or \\~, which is how those memories actually look.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_REPO = _HARNESS.parents[2]
sys.path[:0] = [str(_REPO), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.storage.trados import unescape  # ruff: ignore[module-import-not-at-top-of-file]

RUNS = 7
WARMUP = 2

_SENTENCES = (
    "Open the document and save your changes before you quit.",
    "The selected file could not be found on this computer.",
    "Are you sure you want to replace the existing translation?",
    "Search results for the selected folder are shown below.",
    "Click OK to keep the current preferences.",
)


def _segments() -> list[str]:
    rows: list[str] = []
    for i in range(40000):
        if i % 19 == 0:
            rows.append(f"Quote \\ldblquote{i}\\rdblquote and an emdash\\emdash here.")
        elif i % 47 == 0:
            rows.append(f"Ordre du jour\\~: item {i}")
        else:
            rows.append(f"{_SENTENCES[i % len(_SENTENCES)]} #{i}")
    return rows


def _run(rows: list[str]) -> int:
    total = 0
    for row in rows:
        total += len(unescape(row))
    return total


def main() -> None:
    pin_cpu()
    rows = _segments()
    assert unescape("Ordre du jour\\~:") == "Ordre du jour\u00a0:"
    assert (
        unescape("Association for Road Safety \\endash  Conference")
        == "Association for Road Safety –  Conference"
    )
    assert unescape("plain sentence") == "plain sentence"
    assert "\u2014" in unescape("wait\\emdash now")

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
