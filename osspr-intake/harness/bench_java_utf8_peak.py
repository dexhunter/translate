"""Peak traced memory of java_utf8_properties_encode on one long properties value.

Java UTF-8, Java UTF-16, and Mozilla dialects call this for every value they
write. The input is one help/license-sized translation (CJK and Cyrillic, plus
the newlines and tabs those files actually contain).
"""

from __future__ import annotations

import sys
import tracemalloc
from pathlib import Path

_HARNESS = Path(__file__).resolve().parent
_ROOT = _HARNESS.parents[1]
sys.path[:0] = [str(_ROOT), str(_HARNESS)]

from _stats import full_spread_pct, median, pin_cpu  # noqa: E402
from translate.misc.quote import java_utf8_properties_encode  # noqa: E402

RUNS = 7
WARMUP = 2


def _text() -> str:
    paragraph = (
        "この製品には複数の貢献者によるソフトウェアが含まれています。"
        "設定を確認してからファイルを保存してください。\n"
        "Приложение хранит локальную копию документа и показывает предупреждение, "
        "если есть несохранённые изменения.\t"
        "路径中的反斜杠会按原样保留：C:\\Users\\Public\\文件。\n"
    )
    return paragraph * 40


def _peak(text: str) -> tuple[int, int]:
    tracemalloc.start()
    encoded = java_utf8_properties_encode(text)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, len(encoded)


def main() -> None:
    pin_cpu()
    text = _text()
    assert java_utf8_properties_encode("abc") == "abc"
    assert java_utf8_properties_encode("abcḓ") == "abcḓ"
    assert java_utf8_properties_encode("abc\n") == "abc\\n"
    assert "\\n" in java_utf8_properties_encode("line\nnext")
    assert "\\t" in java_utf8_properties_encode("\tindented")
    assert "\\\\" in java_utf8_properties_encode("C:\\Temp")

    for _ in range(WARMUP):
        _peak(text)
    peaks: list[float] = []
    length = 0
    for _ in range(RUNS):
        peak, length = _peak(text)
        peaks.append(float(peak))
    mid = median(peaks)
    print(
        f"baseline_value={mid:.0f} noise_pct={full_spread_pct(peaks):.4f} "
        f"output_len={length} input_len={len(text)} "
        f"runs={','.join(f'{peak:.0f}' for peak in peaks)}"
    )


if __name__ == "__main__":
    main()
