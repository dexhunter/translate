"""Time quote.extract on lines shaped like a Mozilla DTD file.

dtdfile walks every line and calls extract for entity quotes and comments.
The common call is a matching quote pair with no escape character.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from _stats import full_spread_pct, median, pin_cpu  # noqa: E402
from translate.misc.quote import extract  # noqa: E402

RUNS = 7
WARMUP = 2


def _lines() -> list[tuple[str, str, str]]:
    values = [
        "Save the file before you quit.",
        "Open the preferences for this account.",
        "The document has unsaved changes.",
        "Click OK to continue, or Cancel to go back.",
        'Use the "quoted" name as the title.',
        "It's ready to publish.",
        "Path: C:\\\\Users\\\\Public\\\\file",
        "",
    ]
    rows: list[tuple[str, str, str]] = []
    for i in range(6000):
        value = values[i % len(values)]
        if i % 20 == 0:
            rows.append(
                (
                    f"<!-- Localization note for item {i}: {value} -->\n",
                    "<!--",
                    "-->",
                )
            )
        else:
            quote_char = "'" if i % 15 == 0 else '"'
            rows.append(
                (
                    f"<!ENTITY menu.item.{i} {quote_char}{value}{quote_char}>\n",
                    quote_char,
                    quote_char,
                )
            )
    return rows


def _run(rows: list[tuple[str, str, str]]) -> int:
    total = 0
    # Repeat the file so the sample is long enough for a stable median.
    for _ in range(48):
        for line, start, end in rows:
            extracted, _in_string = extract(
                line, start, end, startinstring=False, allowreentry=False
            )
            total += len(extracted)
    return total


def main() -> None:
    pin_cpu()
    rows = _lines()
    assert extract("the 'quoted' part", "'", "'", "\\", 0) == ("'quoted'", False)
    assert extract("<quoted><again>", "<", ">", "\\", 0)[0] == "<quoted><again>"

    for _ in range(WARMUP):
        _run(rows)
    samples: list[float] = []
    checksum = 0
    for _ in range(RUNS):
        start = time.perf_counter()
        checksum = _run(rows)
        samples.append((time.perf_counter() - start) * 1000.0)
    mid = median(samples)
    print(
        f"median_ms={mid:.4f} noise_pct={full_spread_pct(samples):.4f} "
        f"checksum={checksum} runs={','.join(f'{sample:.4f}' for sample in samples)}"
    )


if __name__ == "__main__":
    main()
