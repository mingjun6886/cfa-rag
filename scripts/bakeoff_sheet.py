"""Builds one local HTML page for reviewing the parser bake-off: each page image beside what
every parser produced for it, with formulas typeset.

The page loads KaTeX from a CDN to typeset formulas, so it needs internet to look its best.
Keep the output under data/: it contains text from the notes.

Run: uv run python scripts/bakeoff_sheet.py --pages evals/parser_bakeoff/pages.yaml \
        --parsed data/parsed --raw "data/raw/NotesLV1 2024" --out data/bakeoff/review.html
"""

import argparse
import base64
import html
import io
from pathlib import Path

import pypdfium2 as pdfium
import yaml

_KATEX = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9"
_HEAD = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Parser bake-off review</title>
<link rel="stylesheet" href="{_KATEX}/katex.min.css">
<style>
 body {{ font: 14px/1.4 system-ui, sans-serif; margin: 16px; }}
 .page {{ border-top: 3px solid #888; padding: 12px 0; }}
 .row {{ display: flex; gap: 12px; align-items: flex-start; }}
 .row > div {{ flex: 1 1 0; min-width: 0; }}
 img {{ max-width: 100%; border: 1px solid #ccc; }}
 .md {{ white-space: pre-wrap; border: 1px solid #ccc; padding: 8px; }}
 h3 {{ margin: 0 0 6px; }} h4 {{ margin: 0 0 4px; }}
</style></head><body><h1>Parser bake-off review</h1>
"""
_TAIL = f"""<script src="{_KATEX}/katex.min.js"></script>
<script src="{_KATEX}/contrib/auto-render.min.js"></script>
<script>renderMathInElement(document.body, {{delimiters: [
 {{left: "$$", right: "$$", display: true}}, {{left: "$", right: "$", display: false}}],
 throwOnError: false}});</script></body></html>
"""


def _page_image(pdf_path: Path, page: int) -> str:
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        image = pdf[page - 1].render(scale=1.2).to_pil()
    finally:
        pdf.close()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def main(pages_yaml: Path, parsed_root: Path, raw_root: Path, out_html: Path) -> None:
    entries = yaml.safe_load(pages_yaml.read_text(encoding="utf-8"))["pages"]
    parsers = (
        sorted(p.name for p in parsed_root.iterdir() if p.is_dir()) if parsed_root.exists() else []
    )
    parts = [_HEAD]
    for entry in entries:
        stem = Path(entry["pdf"]).stem
        label = f"{stem} p{entry['page']} ({entry['category']})"
        parts.append(
            f'<section class="page" id="{html.escape(label)}"><h3>{html.escape(label)}</h3>'
        )
        image = _page_image(raw_root / entry["pdf"], entry["page"])
        parts.append(
            f'<div class="row"><div><h4>page</h4><img alt="page image" src="{image}"></div>'
        )
        for parser in parsers:
            file = parsed_root / parser / stem / f"p{entry['page']:04d}.md"
            text = html.escape(file.read_text(encoding="utf-8") if file.exists() else "(no output)")
            parts.append(f'<div><h4>{html.escape(parser)}</h4><div class="md">{text}</div></div>')
        parts.append("</div></section>")
    parts.append(_TAIL)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pages", type=Path, default=Path("evals/parser_bakeoff/pages.yaml"))
    ap.add_argument("--parsed", type=Path, default=Path("data/parsed"))
    ap.add_argument("--raw", type=Path, default=Path("data/raw/NotesLV1 2024"))
    ap.add_argument("--out", type=Path, default=Path("data/bakeoff/review.html"))
    args = ap.parse_args()
    main(args.pages, args.parsed, args.raw, args.out)
    print(f"wrote {args.out}")
