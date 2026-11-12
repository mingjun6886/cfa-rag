"""Command line entry point for the parse stage: PDF pages in, Markdown files out.

Run: uv run python -m cfa_rag.ingestion.parse --parser textlayer --pdf book.pdf --pages 30,31
"""

import argparse
import sys
import time
from collections.abc import Iterable, Sequence
from pathlib import Path

from langchain_core.documents import Document

from cfa_rag.factory import build_parser


def parse_page_spec(spec: str) -> list[int]:
    """Turn "30,31,45-47" into [30, 31, 45, 46, 47]."""
    pages: set[int] = set()
    try:
        for part in spec.split(","):
            first, dash, last = part.strip().partition("-")
            pages.update(range(int(first), int(last) + 1) if dash else [int(first)])
    except ValueError:
        raise ValueError(f"bad page spec {spec!r}; expected e.g. 30,31,45-47") from None
    return sorted(pages)


def write_pages(docs: Iterable[Document], out_root: Path) -> list[Path]:
    """Write each page to `out_root/<parser>/<pdf stem>/p<NNNN>.md` and return the paths."""
    paths: list[Path] = []
    for doc in docs:
        meta = doc.metadata
        path = out_root / meta["parser"] / Path(meta["source"]).stem / f"p{meta['page']:04d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(doc.page_content, encoding="utf-8")
        paths.append(path)
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cfa_rag.ingestion.parse", description=__doc__)
    ap.add_argument("--parser", required=True, help="parser name, e.g. textlayer")
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--pages", help="e.g. 30,31,45-47; all pages when omitted")
    ap.add_argument("--out", type=Path, default=Path("data/parsed"))
    args = ap.parse_args(argv)
    try:
        pages = parse_page_spec(args.pages) if args.pages else None
        started = time.perf_counter()
        for doc in build_parser(args.parser, args.pdf, pages).lazy_load():
            (path,) = write_pages([doc], args.out)
            now = time.perf_counter()
            print(f"{path}  {now - started:.1f}s")
            started = now
    except (ValueError, RuntimeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
