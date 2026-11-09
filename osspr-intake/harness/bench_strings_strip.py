"""Strip inline comments from a large OS X .strings file, line by line.

``DialectStrings.strip_inline_comments_from_line`` walks every character
of every entry while parsing. Most lines are ``"key" = "value";`` with
no ``/* */`` comment. A few lines carry a real comment, and a few values
contain ``/*`` inside quotes so a correct scan still has to respect
string state.
"""

from translate.storage.properties import DialectStrings

LINES = 200000


def build_lines() -> list[str]:
    lines = []
    for index in range(LINES):
        kind = index % 40
        if kind == 0:
            lines.append(
                f'"key.item.{index}" /* engineer note {index} */ = '
                f'"Value {index} for the settings panel";'
            )
        elif kind == 1:
            lines.append(
                f'"key.item.{index}" = "Value with /* not a comment */ {index}";'
            )
        else:
            lines.append(
                f'"key.section.{index}" = "Open document {index} and save your changes.";'
            )
    return lines


def main() -> None:
    total = 0
    for line in build_lines():
        cleaned, comments = DialectStrings.strip_inline_comments_from_line(line)
        total += len(cleaned) + len(comments)
    if total <= 0:
        raise SystemExit("strip produced no output")


if __name__ == "__main__":
    main()
