"""Time quote.entitydecode on a DTD/HTML-sized batch of translation strings.

Most values are plain text. The rest carry a few named entities, which is the
mix unquotefromdtd and htmlentitydecode see while reading real files.
"""

from __future__ import annotations

import html.entities
import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from _stats import full_spread_pct, median, pin_cpu  # noqa: E402
from translate.misc.quote import entitydecode  # noqa: E402

NAMES = html.entities.name2codepoint
RUNS = 7
WARMUP = 2


def _batch() -> list[str]:
    plain = [
        "Save the file before you quit.",
        "Open the preferences for this account.",
        "The document has unsaved changes.",
        "Click OK to continue, or Cancel to go back.",
        "Could not find the selected folder.",
        "Reload this page to see the latest translation.",
        "Your changes were saved automatically.",
        "This name is already used by another project.",
    ]
    with_entities = [
        "Click &quot;OK&quot; to continue.",
        "Terms &amp; conditions apply to this download.",
        "Copyright &copy; 2024 The Document Foundation.",
        "Use &lt;filename&gt; as the export name.",
        "A &amp; B &amp; C must all be selected.",
        "See the &quot;Help&quot; menu for &amp; details.",
        "&nbsp;Leading space is part of the label.",
        "Size: 50&amp;nbsp;MB remaining.",
    ]
    paragraph = (
        "The application stores a local copy of the file. "
        "If the name contains an ampersand it is written as &amp; "
        "and quotation marks are written as &quot;quotes&quot;. "
        "Copyright &copy; remains in the notice. "
    )
    rows: list[str] = []
    for i in range(1800):
        rows.append(f"{plain[i % len(plain)]} ({i})")
        if i % 4 == 0:
            rows.append(with_entities[i % len(with_entities)])
        if i % 17 == 0:
            rows.append(paragraph)
    return rows


def _run(rows: list[str]) -> int:
    total = 0
    # Repeat the file so the sample is long enough for a stable median.
    for _ in range(80):
        for row in rows:
            total += len(entitydecode(row, NAMES))
    return total


def main() -> None:
    pin_cpu()
    rows = _batch()
    assert entitydecode("&copy;", NAMES) == "©"
    assert entitydecode("plain text", NAMES) == "plain text"
    assert entitydecode("&quot;OK&quot;", NAMES) == '"OK"'

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
