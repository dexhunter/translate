"""Encode a batch of Java .properties values.

``javapropertiesencode`` is the default iso-8859-1 encoder used when a
properties unit is written out. It walks every character in Python, even
when the value is plain text that only needs the control-character
translation table (and a leading-space escape).
"""

from translate.misc.quote import javapropertiesencode

VALUES = 250000


def build_values() -> list[str]:
    values = [
        f"Open document {index} and save your changes." for index in range(VALUES)
    ]
    # Cases the encoder must still get right: leading space, controls, non-latin1.
    values[3] = " leading space"
    values[4] = "line\nbreak\tand a tab"
    values[5] = "Zkouška"
    values[6] = "café"
    return values


def main() -> None:
    total = 0
    for value in build_values():
        total += len(javapropertiesencode(value))
    if total <= 0:
        raise SystemExit("encoder produced no output")


if __name__ == "__main__":
    main()
