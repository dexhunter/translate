"""Time php.phpdecode on a PHP localization-file batch.

Double-quoted strings are the heavier path: seven replace passes plus two
regular expressions, even when the value contains no backslash escapes.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from _stats import full_spread_pct, median, pin_cpu  # noqa: E402
from translate.storage.php import phpdecode  # noqa: E402

RUNS = 7
WARMUP = 2


def _batch() -> list[tuple[str, str]]:
    plain = [
        "Welcome back.",
        "Your inbox has new messages.",
        "Could not save the file.",
        "Delete this conversation?",
        "The password is too short.",
        "Signed in as the site administrator.",
        "Export completed without errors.",
        "Reload the page and try again.",
    ]
    escaped = [
        r"Line one\nLine two",
        r"Column\tvalue",
        r"Say \"hello\" to the user",
        r"Directory C:\\Temp\\export",
        r"\117\143\164\141\154",
        r"\x48\x65\x78",
        "Don't escape me here\\'s",
        r"Mixed \n and \t and \\ end",
    ]
    rows: list[tuple[str, str]] = []
    for i in range(5000):
        if i % 10 == 0:
            rows.append((escaped[i % len(escaped)], '"'))
        elif i % 5 == 0:
            rows.append((f"{plain[i % len(plain)]} ({i})", "'"))
        else:
            rows.append((f"{plain[i % len(plain)]} ({i})", '"'))
    return rows


def _run(rows: list[tuple[str, str]]) -> int:
    total = 0
    # Repeat the file so the sample is long enough for a stable median.
    for _ in range(64):
        for text, quotechar in rows:
            total += len(phpdecode(text, quotechar))
    return total


def main() -> None:
    pin_cpu()
    rows = _batch()
    assert phpdecode(r"\'") == "'"
    assert phpdecode("this is a simple string") == "this is a simple string"
    assert phpdecode(r"\n", quotechar='"') == "\n"
    assert phpdecode(r"\117\143\164\141\154", quotechar='"') == "Octal"

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
