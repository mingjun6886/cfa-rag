"""Parser backed by Docling, with formula enrichment (formula images to LaTeX) switched on."""

from collections.abc import Iterator, Sequence
from pathlib import Path

import pypdfium2 as pdfium
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from cfa_rag.ingestion.parsers._pages import check_pages, contiguous_runs


class DoclingParser(BaseLoader):
    name = "docling"

    def __init__(self, pdf_path: Path, pages: Sequence[int] | None = None) -> None:
        self.pdf_path = pdf_path
        self.pages = pages

    def lazy_load(self) -> Iterator[Document]:
        source = pdfium.PdfDocument(self.pdf_path)
        try:
            wanted = check_pages(self.pages, len(source), self.pdf_path.name)
        finally:
            source.close()
        options = PdfPipelineOptions()
        options.do_formula_enrichment = True
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
        )
        # Docling converts one contiguous range at a time.
        for first, last in contiguous_runs(wanted):
            result = converter.convert(self.pdf_path, page_range=(first, last))
            for number in range(first, last + 1):
                yield Document(
                    page_content=result.document.export_to_markdown(page_no=number),
                    metadata={"source": self.pdf_path.name, "page": number, "parser": self.name},
                )
