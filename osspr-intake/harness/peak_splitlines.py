"""
Peak traced memory of pypo.splitlines on one PO catalog.

The input is a 25,000-message file (header, notes on some entries, ordinary
msgid/msgstr pairs). Parsing a PO file starts by splitting it here.
"""

from __future__ import annotations

import sys
import tracemalloc
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_REPO = _HARNESS.parents[2]
sys.path[:0] = [str(_REPO), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.storage.pypo import pofile, splitlines  # ruff: ignore[module-import-not-at-top-of-file]

RUNS = 7
WARMUP = 2


def _catalog() -> bytes:
    store = pofile()
    for i in range(25000):
        unit = store.addsourceunit(
            f"Message {i} about saving the document before you exit the application."
        )
        unit.target = f"Message {i} traduit avant de quitter l'application."
        if i % 100 == 0:
            unit.addnote(f"Translator note {i}")
    return bytes(store)


def _peak(raw: bytes) -> tuple[int, int, str]:
    tracemalloc.start()
    lines, newline = splitlines(raw)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, len(lines), newline


def main() -> None:
    pin_cpu()
    unusual = (
        b'msgid ""\r\r\nmsgstr ""\r\r\n'
        b'"Content-Type: text/plain; charset=UTF-8\\n"\r\r\n\r\r\n'
        b'msgid "test"\r\r\nmsgstr "rest"\r\r\n'
    )
    unusual_lines, unusual_nl = splitlines(unusual)
    assert unusual_nl == "\r\r\n"
    assert any(b'msgid "test"' in line for line in unusual_lines)

    raw = _catalog()
    assert raw[:3] != b"\xef\xbb\xbf"

    for _ in range(WARMUP):
        _peak(raw)
    peaks: list[float] = []
    line_count = 0
    newline = ""
    for _ in range(RUNS):
        peak, line_count, newline = _peak(raw)
        peaks.append(float(peak))
    mid = median(peaks)
    print(  # ruff: ignore[print]
        f"baseline_value={mid:.0f} noise_pct={full_spread_pct(peaks):.4f} "
        f"lines={line_count} newline={newline!r} input_len={len(raw)} "
        f"runs={','.join(f'{peak:.0f}' for peak in peaks)}"
    )


if __name__ == "__main__":
    main()
