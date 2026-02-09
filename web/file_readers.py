"""Utilities for reading text content from various file formats."""

from __future__ import annotations

from pathlib import Path


def read_instructions_file(data: bytes, filename: str) -> str:
    """Extract text content from an instructions file.

    Supports: .txt, .csv, .md, .xlsx, .doc, .docx, .pdf
    """
    ext = Path(filename).suffix.lower()

    if ext in (".txt", ".csv", ".md"):
        return data.decode("utf-8", errors="replace")

    if ext == ".xlsx":
        return _read_xlsx(data)

    if ext in (".doc", ".docx"):
        return _read_docx(data)

    if ext == ".pdf":
        return _read_pdf(data)

    raise ValueError(f"Unsupported instructions file format: {ext}")


def _read_xlsx(data: bytes) -> str:
    """Read all cell values from an Excel workbook."""
    import io

    try:
        import openpyxl
    except ImportError:
        raise RuntimeError(
            "openpyxl is required to read .xlsx files. "
            "Install it with: pip install openpyxl"
        )

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    lines = []
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None]
            if cells:
                lines.append(" ".join(cells))
    wb.close()
    return "\n".join(lines)


def _read_docx(data: bytes) -> str:
    """Read paragraph text from a Word document."""
    import io

    try:
        import docx
    except ImportError:
        raise RuntimeError(
            "python-docx is required to read .doc/.docx files. "
            "Install it with: pip install python-docx"
        )

    doc = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_pdf(data: bytes) -> str:
    """Read text from a PDF file."""
    import io

    try:
        import PyPDF2
    except ImportError:
        raise RuntimeError(
            "PyPDF2 is required to read .pdf files. "
            "Install it with: pip install PyPDF2"
        )

    reader = PyPDF2.PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)
