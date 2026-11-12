"""Parser that keeps the PDF's own text and sends only the formula images to a reader model.

Body text is never re-recognised, so it stays exact. Text comes from pdfium, because pdfminer
(used by pdfplumber) drops the "fi" and "fl" ligature glyphs in these PDFs. Images are
classified as follows:
an image whose raw bytes occur three or more times in the PDF is decoration and is dropped;
every other image goes to the formula reader and is placed back in reading order.
"""

import hashlib
import io
import logging
import re
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import pdfplumber
import pypdfium2 as pdfium
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from cfa_rag.factory import build_formula_reader
from cfa_rag.ingestion.parsers._pages import check_pages

logger = logging.getLogger(__name__)

_DECORATION_MIN_USES = 3
_RENDER_DPI = 200
_LINE_JOIN = "\n"
_UNREADABLE = "[formula unreadable]"
_FIGURE = "[figure]"
_NOT_A_FORMULA = "NOT_A_FORMULA"
_FENCE = re.compile(r"```[A-Za-z]*\n?(.*?)\n?```", re.DOTALL)


def _clean(raw: str) -> str:
    """Strip whitespace, a surrounding code fence and surrounding dollar signs."""
    text = raw.strip()
    fenced = _FENCE.fullmatch(text)
    if fenced:
        text = fenced.group(1).strip()
    return text.strip("$").strip()


def _words(pdfium_page: Any) -> list[dict[str, Any]]:
    """Words with boxes in pdfplumber's coordinates (origin top left), read through pdfium."""
    height = pdfium_page.get_height()
    textpage = pdfium_page.get_textpage()
    words: list[dict[str, Any]] = []
    chars: list[str] = []
    boxes: list[tuple[float, float, float, float]] = []

    def flush() -> None:
        if chars:
            lefts, bottoms, rights, tops = zip(*boxes, strict=True)
            words.append(
                {
                    "text": "".join(chars),
                    "x0": min(lefts),
                    "x1": max(rights),
                    "top": height - max(tops),
                    "bottom": height - min(bottoms),
                }
            )
        chars.clear()
        boxes.clear()

    for index in range(textpage.count_chars()):
        char = textpage.get_text_range(index, 1)
        if not char or char.isspace() or ord(char[0]) < 32:  # whitespace and control chars
            flush()
        else:
            chars.append(char)
            boxes.append(textpage.get_charbox(index))
    flush()
    textpage.close()
    return words


def _image_key(image: dict[str, Any]) -> str:
    return hashlib.sha1(image["stream"].get_rawdata()).hexdigest()


class TextLayerParser(BaseLoader):
    name = "textlayer"

    def __init__(
        self,
        pdf_path: Path,
        pages: Sequence[int] | None = None,
        formula_reader: Callable[[bytes], str] | None = None,
    ) -> None:
        self.pdf_path = pdf_path
        self.pages = pages
        self._reader = formula_reader

    def lazy_load(self) -> Iterator[Document]:
        with pdfplumber.open(self.pdf_path) as pdf:
            wanted = check_pages(self.pages, len(pdf.pages), self.pdf_path.name)
            text_pdf = pdfium.PdfDocument(self.pdf_path)
            try:
                decoration: set[str] | None = None
                for number in wanted:
                    page = pdf.pages[number - 1]
                    images = page.images
                    if images and decoration is None:
                        decoration = self._decoration_keys(pdf)
                    keep = [im for im in images if _image_key(im) not in (decoration or set())]
                    text_page = text_pdf[number - 1]
                    words = _words(text_page)
                    text_page.close()
                    yield Document(
                        page_content=self._render(page, number, keep, words),
                        metadata={
                            "source": self.pdf_path.name,
                            "page": number,
                            "parser": self.name,
                        },
                    )
                    page.flush_cache()
            finally:
                text_pdf.close()

    @staticmethod
    def _decoration_keys(pdf: Any) -> set[str]:
        # shortcut: scans every page once per run to count image reuse; cache the counts on
        # disk if parsing a few pages of a large book becomes slow.
        uses: Counter[str] = Counter()
        for page in pdf.pages:
            uses.update(_image_key(im) for im in page.images)
            page.flush_cache()
        return {key for key, count in uses.items() if count >= _DECORATION_MIN_USES}

    def _render(
        self, page: Any, number: int, images: list[dict[str, Any]], words: list[dict[str, Any]]
    ) -> str:
        lines = self._lines(words)
        display: list[tuple[float, str]] = []
        for image in images:
            text, is_latex = self._read_formula(page, number, image)
            line = self._line_for(lines, image)
            if line is not None:
                line["parts"].append((image["x0"], f"${text}$" if is_latex else text))
            else:
                display.append((image["top"], f"$${text}$$" if is_latex else text))
        rows = [(ln["top"], " ".join(t for _, t in sorted(ln["parts"]))) for ln in lines]
        return _LINE_JOIN.join(text for _, text in sorted(rows + display, key=lambda r: r[0]))

    @staticmethod
    def _lines(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Group words into lines by vertical position; each line keeps (x, text) parts."""
        lines: list[dict[str, Any]] = []
        for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
            centre = (word["top"] + word["bottom"]) / 2
            line = lines[-1] if lines else None
            if line is not None and line["top"] <= centre <= line["bottom"]:
                line["top"] = min(line["top"], word["top"])
                line["bottom"] = max(line["bottom"], word["bottom"])
            else:
                line = {"top": word["top"], "bottom": word["bottom"], "parts": []}
                lines.append(line)
            line["parts"].append((word["x0"], word["text"]))
        return lines

    @staticmethod
    def _line_for(lines: list[dict[str, Any]], image: dict[str, Any]) -> dict[str, Any] | None:
        """The text line an image sits inside (at least half the line's height), if any."""
        best, best_overlap = None, 0.0
        for line in lines:
            overlap = min(line["bottom"], image["bottom"]) - max(line["top"], image["top"])
            if overlap >= 0.5 * (line["bottom"] - line["top"]) and overlap > best_overlap:
                best, best_overlap = line, overlap
        return best

    def _read_formula(self, page: Any, number: int, image: dict[str, Any]) -> tuple[str, bool]:
        """Return (text, is_latex) for one image; markers are never LaTeX."""
        box = (
            max(image["x0"], 0.0),
            max(image["top"], 0.0),
            min(image["x1"], float(page.width)),
            min(image["bottom"], float(page.height)),
        )
        buffer = io.BytesIO()
        page.crop(box).to_image(resolution=_RENDER_DPI).original.save(buffer, format="PNG")
        try:
            if self._reader is None:
                self._reader = build_formula_reader()
            cleaned = _clean(self._reader(buffer.getvalue()))
        except Exception as error:  # a failed formula must not lose the whole page
            logger.warning("formula reader failed on page %d: %s", number, error)
            return _UNREADABLE, False
        if not cleaned:
            return _UNREADABLE, False
        if cleaned == _NOT_A_FORMULA:
            return _FIGURE, False
        return cleaned, True
