import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import pytest

from cfa_rag.ingestion.parsers._pages import contiguous_runs
from cfa_rag.ingestion.parsers.docling_parser import DoclingParser
from cfa_rag.ingestion.parsers.mistral_parser import MistralParser

FIXTURE = Path(__file__).parent / "fixtures" / "text_and_images.pdf"


@dataclass
class FakePage:
    index: int
    markdown: str


@dataclass
class FakeResponse:
    pages: list[FakePage]


@dataclass
class FakeOcr:
    pages: list[FakePage]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def process(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return FakeResponse(self.pages)


@dataclass
class FakeMistral:
    ocr: FakeOcr


def test_contiguous_runs() -> None:
    assert contiguous_runs([1, 2, 3, 7, 9, 10]) == [(1, 3), (7, 7), (9, 10)]
    assert contiguous_runs([]) == []


@pytest.mark.slow
def test_docling_yields_one_document_per_page_with_text() -> None:
    docs = list(DoclingParser(FIXTURE).lazy_load())
    assert [d.metadata["page"] for d in docs] == [1, 2, 3]
    assert all(d.metadata["parser"] == "docling" for d in docs)
    assert all(d.metadata["source"] == "text_and_images.pdf" for d in docs)
    assert "Before formula" in docs[0].page_content and "Plain page 2" in docs[1].page_content


@pytest.mark.slow
def test_docling_keeps_original_page_numbers_for_a_selection() -> None:
    docs = list(DoclingParser(FIXTURE, pages=[3]).lazy_load())
    assert [d.metadata["page"] for d in docs] == [3]
    assert "Plain page 3" in docs[0].page_content


def test_docling_page_out_of_range() -> None:
    with pytest.raises(ValueError, match=r"page 9 out of range: text_and_images\.pdf has 3 pages"):
        list(DoclingParser(FIXTURE, pages=[9]).lazy_load())


def test_mistral_sends_only_requested_pages_and_maps_indices_back() -> None:
    client = FakeMistral(FakeOcr([FakePage(0, "one"), FakePage(1, "three")]))
    docs = list(MistralParser(FIXTURE, pages=[1, 3], client=client).lazy_load())
    assert [(d.metadata["page"], d.page_content, d.metadata["parser"]) for d in docs] == [
        (1, "one", "mistral"),
        (3, "three", "mistral"),
    ]
    sent = client.ocr.calls[0]["document"]
    assert sent["type"] == "document_url"
    prefix = "data:application/pdf;base64,"
    assert sent["document_url"].startswith(prefix)
    subset = pdfium.PdfDocument(base64.b64decode(sent["document_url"][len(prefix) :]))
    assert len(subset) == 2  # the other page never leaves the machine


def test_mistral_rejects_a_response_that_does_not_match_the_request() -> None:
    client = FakeMistral(FakeOcr([FakePage(0, "only one")]))
    with pytest.raises(RuntimeError, match="returned pages"):
        list(MistralParser(FIXTURE, pages=[1, 3], client=client).lazy_load())


def test_mistral_page_out_of_range() -> None:
    with pytest.raises(ValueError, match="page 9 out of range"):
        list(MistralParser(FIXTURE, pages=[9], client=FakeMistral(FakeOcr([]))).lazy_load())


def test_mistral_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY is not set"):
        list(MistralParser(FIXTURE).lazy_load())
