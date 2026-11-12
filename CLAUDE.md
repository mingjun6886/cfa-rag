# CFA RAG

Ask-my-docs system over CFA Level I study notes: retrieve the right passages and answer with
citations (book, reading, page), and decline when the retrieved text does not support an answer.
Public portfolio project. Status on 2026-11-12: scaffold only, no pipeline code yet.

A full design is awaiting the owner's approval in `docs/design.md`, with the reasoning in
`docs/tech-decisions.md`. Where they differ from the Roadmap, Stack and Architecture sections
below, they win once approved, and this file is then updated to match.

Talk to the user in Vietnamese. Code, comments, commit messages and docs are in English.

## Corpus

`data/raw/NotesLV1 2024/` holds SchweserNotes 2024 Level I, Books 1–5 (1,145 pages), and the
QuickSheet (6 pages). Checked on the files themselves:

- The books are calibre-generated PDFs with a clean text layer. Body text needs no OCR.
- **Formulas are embedded images.** Plain text extraction drops them and leaves a blank line
  (see Book 1, p.30). The parser must turn formula images into LaTeX, in reading order.
- Page numbers must survive parsing, because citations depend on them.

The notes are copyrighted. `data/` is gitignored: never commit source PDFs, parsed text, chunks or
an index. The repository is public, so nothing committed may quote the notes, including the
golden set and eval reports.

## Roadmap

| Phase | Work | Done when |
|---|---|---|
| 0 | Parser bake-off on ~20 pages (formula-heavy, table-heavy, plain). 25–30 hand-checked questions. Script for hit@k and MRR. | A parser is chosen on evidence and the metric script runs |
| 1 | Parse → chunk → embed → index → retrieve → answer with citations. CLI only. | Baseline numbers are recorded |
| 2 | Hybrid retrieval (dense + BM25, RRF), cross-encoder rerank, citation enforcement and refusal, versioned prompts, query rewrite for Vietnamese questions | Each step is kept only if it beats the baseline |
| 3 | Golden set of 100–200 questions; faithfulness, correctness and refusal accuracy; CI gate | A PR that lowers quality fails the build |

Only PDF ingestion is in scope. Markdown and web loaders wait until such a source exists.

## Stack

Proposed on 2026-11-12 and not yet confirmed by the user. Ask before adding a dependency.

| Role | Proposed | Alternatives |
|---|---|---|
| Parser | Docling, to be confirmed by the Phase 0 bake-off | PyMuPDF text + formula-image OCR; Mistral OCR |
| Embedding | `BAAI/bge-m3` via sentence-transformers (local, multilingual) | Voyage, OpenAI |
| Vector store | Qdrant in local mode (`QdrantClient(path=...)`) | LanceDB, Chroma |
| Keyword search | BM25 sparse vectors in the same Qdrant collection, fused with RRF | — |
| Reranker | `BAAI/bge-reranker-v2-m3` via sentence-transformers `CrossEncoder` | Cohere Rerank |
| Generator | Claude API (`anthropic` SDK) with Citations; model id lives in config | Ollama, for offline work |
| Orchestration | Plain Python; LangGraph once the query flow has branches or loops | — |
| Evaluation | Own hit@k and MRR, plus DeepEval faithfulness under pytest | Ragas |
| Tooling | uv, ruff, mypy, pytest | — |

Qdrant hybrid queries: put the metadata filter inside each `Prefetch`. A top-level `query_filter`
did not constrain a fusion query in local mode (qdrant-client 1.16.2).

## Architecture rules

The goal is that replacing a technology means writing one file and changing one config line.

- `src/cfa_rag/models.py` holds the domain types. Only these cross module boundaries.
- `src/cfa_rag/ports.py` holds one `typing.Protocol` per swappable role: parser, chunker,
  embedder, index, reranker, generator.
- An adapter is one file per technology, named `<tech>_<role>.py`
  (`ingestion/parsers/docling_parser.py`). Vendor SDKs are imported only inside adapter files.
- Everything else depends on `models` and `ports` only. No LangChain or vendor type appears in a
  function signature outside an adapter.
- One factory maps a config string to an adapter and imports it lazily, so an unused backend's
  dependencies are not required.
- Ingestion stages write to disk and re-run independently: `data/parsed/<parser>/` →
  chunks → `data/index/`. Switching parser must not overwrite another parser's output, and
  re-chunking must not re-parse.
- Chunk by document structure (reading → section), aiming for 500–800 tokens. Never split a
  formula, table or worked example. Every chunk carries book, topic, reading, section, page range
  and kind (text, example, quiz, answer key).

## Conventions

- Settings live in `configs/`, secrets in `.env`. No model name, top-k or threshold is hardcoded.
- Prompts live in `configs/prompts/<name>.v<N>.yaml`. A released version is never edited; a change
  is a new version. Every answer and every eval result records the prompt version it used.
- An eval result also records the git commit and the config it ran with.
- Full type hints; `mypy --strict` and `ruff` must pass.
- Unit tests use fakes that implement the ports and never touch the network.
- A new step in the pipeline (reranker, rewrite, larger top-k) ships with its before/after numbers.

## Commands

```bash
uv sync                  # install
uv run pytest            # tests
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy              # type check
```

## Git

Conventional Commits, no attribution trailers. Do not push or open a PR unless asked.
Everything goes to the GitHub account `mingjun6886`; this repository's local git identity is set
to it. SSH on this machine authenticates as another account, so use an HTTPS remote.
