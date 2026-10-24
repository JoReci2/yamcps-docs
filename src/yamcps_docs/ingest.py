"""Explicit offline ingestion from a complete JSON manifest."""

import importlib
import json
import sys
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from yamcps.rag import Document, RetrievalIndex


class Source(BaseModel):
    """One source revision under the manifest directory."""

    model_config = ConfigDict(extra="forbid")
    path: str
    document_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class Manifest(BaseModel):
    """Complete desired snapshot of exactly one corpus."""

    model_config = ConfigDict(extra="forbid")
    corpus: str = Field(min_length=1)
    sources: list[Source]


def _source_path(root: Path, name: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Source paths must stay below the manifest directory")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Source symlinks are not supported")
    path = current.resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Source must be a file below the manifest directory")
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("Source exceeds the 20 MiB limit")
    return path


def _column_name(column: int) -> str:
    name = ""
    while column:
        column, remainder = divmod(column - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _excel_text(sheets: Iterable[tuple[str, Iterable[Iterable[Any]]]]) -> str:
    lines: list[str] = []
    characters = 0
    scanned = 0
    for title, rows in sheets:
        started = False
        for row_number, row in enumerate(rows, 1):
            values = []
            for column, value in enumerate(row, 1):
                scanned += 1
                if scanned > 1_000_000:
                    raise ValueError("Excel source exceeds 1 million scanned cells")
                if value is None or value == "":
                    continue
                text = value.isoformat() if isinstance(value, (date, datetime)) else str(value)
                cell = f"{_column_name(column)}{row_number}: {text}"
                characters += len(cell) + 3
                if characters > 4_000_000:
                    raise ValueError("Source exceeds 4 million extracted characters")
                values.append(cell)
            if values:
                if not started:
                    heading = f"Sheet: {title}"
                    characters += len(heading) + 1
                    lines.append(heading)
                    started = True
                lines.append(" | ".join(values))
    return "\n".join(lines)


def _extract_excel(path: Path) -> str:
    if path.suffix.lower() == ".xlsx":
        workbook = importlib.import_module("openpyxl").load_workbook(
            str(path), read_only=True, data_only=False, keep_links=False
        )
        try:
            return _excel_text(
                (sheet.title, sheet.iter_rows(values_only=True)) for sheet in workbook.worksheets
            )
        finally:
            workbook.close()
    xlrd = importlib.import_module("xlrd")

    def rows(sheet: Any, datemode: int) -> Iterable[list[Any]]:
        for row_number in range(sheet.nrows):
            values = []
            for cell in sheet.row(row_number):
                value = cell.value
                if cell.ctype == xlrd.XL_CELL_DATE:
                    value = xlrd.xldate_as_datetime(value, datemode)
                elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                    value = bool(value)
                elif cell.ctype == xlrd.XL_CELL_ERROR:
                    value = xlrd.error_text_from_code.get(value, "#ERROR!")
                values.append(value)
            yield values

    with xlrd.open_workbook(str(path), on_demand=True, logfile=sys.stderr) as workbook:

        def sheets() -> Iterable[tuple[str, Iterable[list[Any]]]]:
            for number in range(workbook.nsheets):
                sheet = workbook.sheet_by_index(number)
                yield sheet.name, rows(sheet, workbook.datemode)
                workbook.unload_sheet(number)

        return _excel_text(sheets())


def _extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        reader = importlib.import_module("pypdf").PdfReader(str(path))
        return "\n\f\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        document = importlib.import_module("docx").Document(str(path))
        paragraphs = [p.text for p in document.paragraphs]
        tables = [
            " | ".join(c.text for c in row.cells) for table in document.tables for row in table.rows
        ]
        return "\n".join(paragraphs + tables)
    if suffix in {".xlsx", ".xls"}:
        return _extract_excel(path)
    raise ValueError("Supported source formats: .txt, .md, .pdf, .docx, .xlsx, .xls")


def ingest(index: RetrievalIndex, manifest_path: Path, *, chunk_size: int = 1200) -> dict[str, int]:
    """Extract all sources before atomically synchronizing a corpus.

    Args:
        index: Configured retrieval index.
        manifest_path: JSON manifest, relative paths resolved against its directory.
        chunk_size: Maximum extracted characters per passage.

    Returns:
        Updated, unchanged and deleted document counts.

    Raises:
        ValueError: Manifest, source path, format or extracted content is invalid.
    """
    manifest = Manifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    root = manifest_path.resolve(strict=True).parent
    documents = []
    for source in manifest.sources:
        path = _source_path(root, source.path)
        text = _extract(path)
        if not text.strip() or len(text) > 4_000_000:
            raise ValueError(
                "Source is empty or exceeds 4 million extracted characters; OCR is not included"
            )
        documents.append(
            Document(
                corpus=manifest.corpus,
                document_id=source.document_id,
                revision=source.revision,
                text=text,
                metadata=source.metadata,
            )
        )
    return index.sync(manifest.corpus, documents, chunk_size=chunk_size)
