"""Fails if any golden question or reference answer copies 8 or more consecutive words of the notes.

Run: uv run python scripts/check_no_verbatim.py --golden evals/golden/cfa_l1.jsonl --notes data/raw
"""

import argparse
import sys
from pathlib import Path

import pypdfium2 as pdfium

from cfa_rag.evaluation.golden import load_golden
from cfa_rag.evaluation.verbatim import find_copied


def notes_text(notes_dir: Path) -> str:
    parts: list[str] = []
    for pdf_path in sorted(notes_dir.rglob("*.pdf")):
        pdf = pdfium.PdfDocument(pdf_path)
        try:
            parts.extend(page.get_textpage().get_text_range() for page in pdf)
        finally:
            pdf.close()
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--golden", required=True, type=Path)
    ap.add_argument("--notes", required=True, type=Path, help="folder holding the notes' PDFs")
    args = ap.parse_args()
    corpus = notes_text(args.notes)
    if not corpus.strip():
        print(f"error: no text found under {args.notes}", file=sys.stderr)
        return 2
    copied = find_copied(load_golden(args.golden), corpus)
    for item_id, grams in sorted(copied.items()):
        print(f"{item_id}: {len(grams)} shared 8-word sequence(s)")
    return 1 if copied else 0


if __name__ == "__main__":
    raise SystemExit(main())
