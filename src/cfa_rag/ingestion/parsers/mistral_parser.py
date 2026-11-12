"""Parser backed by the Mistral OCR API.

Only the requested pages are sent: they are cut into a small PDF first, so the rest of the book
never leaves the machine.
"""

import base64
import io
import os
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from cfa_rag.ingestion.parsers._pages import check_pages

_DEFAULT_MODEL = "mistral-ocr-latest"


def _build_client() -> Any:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        raise RuntimeError("MISTRAL_API_KEY is not set")
    from mistralai.client import Mistral

    return Mistral(api_key=key)


def _subset_data_url(pdf_path: Path, pages: Sequence[int]) -> str:
    """A base64 data URL of a PDF holding only `pages` (1-indexed) of `pdf_path`."""
    source = pdfium.PdfDocument(pdf_path)
    subset = pdfium.PdfDocument.new()
    try:
        subset.import_pages(source, [page - 1 for page in pages])
        buffer = io.BytesIO()
        subset.save(buffer)
    finally:
        subset.close()
        source.close()
    return "data:application/pdf;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


class MistralParser(BaseLoader):
    name = "mistral"

    def __init__(
        self, pdf_path: Path, pages: Sequence[int] | None = None, client: Any | None = None
    ) -> None:
        self.pdf_path = pdf_path
        self.pages = pages
        self._client = client

    def lazy_load(self) -> Iterator[Document]:
        source = pdfium.PdfDocument(self.pdf_path)
        try:
            wanted = check_pages(self.pages, len(source), self.pdf_path.name)
        finally:
            source.close()
        client = self._client or _build_client()
        response = client.ocr.process(
            model=os.environ.get("CFA_RAG_MISTRAL_MODEL", _DEFAULT_MODEL),
            document={
                "type": "document_url",
                "document_url": _subset_data_url(self.pdf_path, wanted),
            },
        )
        markdown = {page.index: page.markdown for page in response.pages}
        if sorted(markdown) != list(range(len(wanted))):
            raise RuntimeError(
                f"Mistral returned pages {sorted(markdown)} for {len(wanted)} requested pages"
            )
        for position, number in enumerate(wanted):
            yield Document(
                page_content=markdown[position],
                metadata={"source": self.pdf_path.name, "page": number, "parser": self.name},
            )
