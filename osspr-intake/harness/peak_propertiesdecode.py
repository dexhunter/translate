"""Peak traced memory of decoding one long Java properties value.

``propertiesdecode`` appends every character onto a Python list, then
joins it, including values that contain no backslash escapes. Prop2po
and unit.source do this for every value. The workload is one long
unescaped help string, about the size of a bundled legal or HTML
template stored as a single property.
"""

import tracemalloc

from translate.misc.quote import propertiesdecode

SENTENCE = "Open the document and save your changes before you continue. "
REPEATS = 30000


def main() -> None:
    value = SENTENCE * REPEATS
    tracemalloc.start()
    tracemalloc.reset_peak()
    decoded = propertiesdecode(value)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if decoded != value:
        raise SystemExit("decoder changed an unescaped value")
    print(peak)


if __name__ == "__main__":
    main()
