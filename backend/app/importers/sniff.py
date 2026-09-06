"""File-format detection. Korean card companies routinely export HTML
tables with a `.xls` extension, and sometimes double-append `.xlsx`, so
the file extension cannot be trusted - we sniff the actual bytes."""

from pathlib import Path

_ZIP_MAGIC = b"PK\x03\x04"  # xlsx/docx/... are zip containers


def is_real_xlsx(file_path: Path) -> bool:
    with file_path.open("rb") as f:
        head = f.read(4)
    return head == _ZIP_MAGIC


def is_html(file_path: Path) -> bool:
    # Some exports (e.g. 현대카드) pad the file with a large JS/CSS
    # preamble before the actual <html> tag, so a small prefix isn't
    # enough - these files are small bank exports, so reading a
    # generous chunk is still cheap.
    with file_path.open("rb") as f:
        head = f.read(200_000)
    lowered = head.lower()
    return b"<html" in lowered or b"<table" in lowered


def is_pdf(file_path: Path) -> bool:
    with file_path.open("rb") as f:
        head = f.read(5)
    return head == b"%PDF-"
