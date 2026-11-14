"""
Time mofile.serialize on a catalog the size of a shipped application.

The file is a header plus 6000 translated messages: UI sentences, a context
on every 20th message, a plural every 40th message, and a few blank targets.
"""

from __future__ import annotations

import struct
import sys
import time
from io import BytesIO
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_REPO = _HARNESS.parents[2]
sys.path[:0] = [str(_REPO), str(_HARNESS)]

from stats import full_spread_pct, median, pin_cpu  # ruff: ignore[module-import-not-at-top-of-file]

from translate.misc.multistring import multistring  # ruff: ignore[module-import-not-at-top-of-file]
from translate.storage.mo import MO_MAGIC_NUMBER, mofile  # ruff: ignore[module-import-not-at-top-of-file]

RUNS = 7
WARMUP = 2


def _catalog() -> mofile:
    store = mofile()
    header = store.addsourceunit("")
    header.target = (
        "Project-Id-Version: app\n"
        "POT-Creation-Date: 2020-01-01 00:00+0000\n"
        "Content-Type: text/plain; charset=UTF-8\n"
    )
    sentences = (
        "Open the document and save your changes.",
        "The file could not be found.",
        "Are you sure you want to quit?",
        "Search results for the selected folder.",
        "Preferences",
    )
    for i in range(6000):
        if i % 40 == 0:
            unit = store.addsourceunit("one file")
            unit.source = multistring(["one file", "%d files"])
            unit.target = multistring(["un fichier", "%d fichiers"])
        else:
            unit = store.addsourceunit(f"{sentences[i % len(sentences)]} #{i}")
            if i % 55 == 0:
                unit.target = ""
            else:
                unit.target = f"Traduction {i} du texte source."
        if i % 20 == 0:
            unit.setcontext(f"menu.file.{i}")
    return store


def _run(store: mofile) -> bytes:
    out = BytesIO()
    store.serialize(out)
    return out.getvalue()


def main() -> None:
    pin_cpu()
    store = _catalog()
    blob = _run(store)
    assert blob[:4] == struct.pack("I", MO_MAGIC_NUMBER)
    assert len(blob) > 100_000

    for _ in range(WARMUP):
        _run(store)
    samples: list[float] = []
    checksum = 0
    for _ in range(RUNS):
        start = time.perf_counter()
        blob = _run(store)
        samples.append((time.perf_counter() - start) * 1000.0)
        checksum = len(blob)
    mid = median(samples)
    print(  # ruff: ignore[print]
        f"median_ms={mid:.4f} noise_pct={full_spread_pct(samples):.4f} "
        f"checksum={checksum} runs={','.join(f'{sample:.4f}' for sample in samples)}"
    )


if __name__ == "__main__":
    main()
