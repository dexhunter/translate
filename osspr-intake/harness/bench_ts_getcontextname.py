"""Parse a large single-context Qt TS file.

``tsunit.getcontextname`` runs once per message and looks the context
``<name>`` up with ``Element.find``, which walks every sibling in the
context. One context with thousands of messages is a normal lupdate
layout (one class or one generated context).
"""

from io import BytesIO

from translate.storage.ts2 import tsfile

MESSAGES = 12000


def build_ts() -> bytes:
    chunks = [
        '<?xml version="1.0" encoding="utf-8"?>\n',
        "<!DOCTYPE TS>\n",
        '<TS version="2.1" language="fr_FR">\n',
        "<context>\n",
        "<name>MainWindow</name>\n",
    ]
    for index in range(MESSAGES):
        chunks.append(
            "<message>\n"
            f'<location filename="src/mainwindow.cpp" line="{index}"/>\n'
            f"<source>Save changes to document {index}</source>\n"
            f"<translation>Enregistrer le document {index}</translation>\n"
            "</message>\n"
        )
    chunks.append("</context>\n</TS>\n")
    return "".join(chunks).encode()


def main() -> None:
    store = tsfile(BytesIO(build_ts()))
    if len(store.units) != MESSAGES:
        raise SystemExit(f"expected {MESSAGES} units, got {len(store.units)}")
    # Touch the result getcontextname already computed during parse.
    if store.units[0].getcontextname() != "MainWindow":
        raise SystemExit("context name was not parsed")


if __name__ == "__main__":
    main()
