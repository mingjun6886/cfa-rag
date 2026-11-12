"""The one place that maps configuration strings to concrete implementations.

Each backend is imported lazily, so an unused backend's dependencies are not required.
"""

import os
from collections.abc import Callable, Sequence
from pathlib import Path

from langchain_core.document_loaders import BaseLoader

PARSER_NAMES = ("docling", "mistral", "textlayer")


def build_parser(name: str, pdf_path: Path, pages: Sequence[int] | None = None) -> BaseLoader:
    """Build the parser called `name` for `pdf_path`, restricted to `pages` when given."""
    if name == "docling":
        from cfa_rag.ingestion.parsers.docling_parser import DoclingParser

        return DoclingParser(pdf_path, pages)
    if name == "mistral":
        from cfa_rag.ingestion.parsers.mistral_parser import MistralParser

        return MistralParser(pdf_path, pages)
    if name == "textlayer":
        from cfa_rag.ingestion.parsers.textlayer_parser import TextLayerParser

        return TextLayerParser(pdf_path, pages)
    raise ValueError(f"unknown parser {name!r}; known parsers: {', '.join(PARSER_NAMES)}")


def build_formula_reader() -> Callable[[bytes], str]:
    """Build the function that turns a formula image (PNG bytes) into LaTeX."""
    model = os.environ.get("CFA_RAG_FORMULA_MODEL")
    if not model:
        raise RuntimeError("CFA_RAG_FORMULA_MODEL is not set")
    from cfa_rag.ingestion.parsers.ollama_formula_reader import make_formula_reader

    return make_formula_reader(model)
