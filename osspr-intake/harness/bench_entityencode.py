"""
Time quote.entityencode on a DTD-sized batch of translation strings.

po2dtd calls this for every entity value, and htmlentityencode uses the same
loop. Most values are plain text. A few contain '%', '&', or an existing entity.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.misc.quote import entityencode  # ruff: ignore[module-import-not-at-top-of-file]

# Same map quotefordtd passes for ordinary DTD text: '%' and '&'.
DTD_CODEPOINT2NAME = {
    ord("%"): "#037",
    ord("&"): "amp",
}

RUNS = 7
WARMUP = 2
# Repeat one large DTD so the median is stable. 6_000 entities is one file.
REPEATS = 8


def _batch() -> list[str]:
    plain = "Open the document and save your changes before you continue."
    rows: list[str] = []
    for i in range(6000):
        if i % 15 == 0:
            rows.append(f'Open "document" {i} & save your changes. Progress {i}%.')
        elif i % 9 == 0:
            rows.append(f"Click &quot;OK&quot; to save file {i}.")
        elif i % 21 == 0:
            rows.append(f"Terms &amp; conditions apply to download {i}.")
        elif i % 40 == 0:
            rows.append(f"a&b&c item {i}")
        else:
            rows.append(f"{plain} ({i})")
    return rows


def _run(rows: list[str]) -> int:
    total = 0
    mapping = DTD_CODEPOINT2NAME
    for _ in range(REPEATS):
        for row in rows:
            total += len(entityencode(row, mapping))
    return total


def main() -> None:
    pin_cpu()
    rows = _batch()
    mapping = DTD_CODEPOINT2NAME
    assert entityencode("plain text", mapping) == "plain text"
    assert entityencode("50% done", mapping) == "50&#037; done"
    assert entityencode("Terms &amp; conditions", mapping) == "Terms &amp; conditions"
    # A later '&' discards the open entity. The benchmark must keep that.
    assert entityencode("a&b&c", mapping) == "a&amp;c"
    assert entityencode("&", mapping) == "&amp;"

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
