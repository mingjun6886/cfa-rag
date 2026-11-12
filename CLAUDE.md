# CFA RAG

Ask-my-docs system over CFA Level I study notes: retrieve the right passages and answer with
citations (book, reading, page), and decline when the retrieved text does not support an answer.
Public portfolio project for AI engineering roles.

The approved design is `docs/design.md`; the reasoning behind each technology choice is
`docs/tech-decisions.md`; code and prompt conventions are `docs/conventions.md`. Read the design
before changing anything. Where this file and the design differ, the design wins.

Talk to the user in Vietnamese. Code, comments, commit messages and docs are in English.

## Shape of the system

- The question flow is served over an HTTP API (`api/openapi.yaml` is the contract). The chat UI
  and the eval harness are clients of that API.
- The serving path is built twice behind the same contract: Python first (milestones 1–3), then
  Rust in `rust/` (milestone 4). Ingestion, evaluation and the UI stay in Python.
- Question flow: input check → rewrite → hybrid search → rerank → grounding gate → answer →
  citation check → respond. Three steps can refuse.
- Every statement in an answer carries a citation (chunk id and verbatim quote) that code checks.

## Corpus

`data/raw/NotesLV1 2024/` holds SchweserNotes 2024 Level I, Books 1–5 (1,145 pages), and the
QuickSheet (6 pages). Checked on the files themselves:

- The books have a clean text layer. Body text needs no OCR.
- **Formulas are embedded images.** Plain text extraction drops them and leaves a blank line
  (Book 1, p.30). The parser must turn formula images into LaTeX, in reading order.
- Page numbers must survive parsing, because citations depend on them.

The notes are copyrighted. `data/` is gitignored. This repository is public, so nothing committed
may quote the notes: no source PDFs, parsed text, chunks or index, and no verbatim passages in the
golden set or in eval reports.

## Milestones

| # | Work | Done when |
|---|---|---|
| 0 | Public foundation: docs, flow page, parser bake-off, sample corpus, first golden questions, retrieval metrics | Repository is public and a parser is chosen on evidence |
| 1 | Walking skeleton: ingest, dense retrieval, cited answer, HTTP API, UI, tracing | A question gets a cited answer in the UI, with a trace |
| 2 | Hybrid search, rerank, grounding gate, rewrite, conversation list | Each step is kept only if it beats the baseline |
| 3 | Evals and safety in CI: golden set of 100–200, attack set, gate | A PR that lowers a gated metric fails |
| 4 | Rust serving path | Contract tests pass; metrics within tolerance of Python |
| 5 | Later: Claude API, other loaders, React UI | — |

## Stack

| Role | Choice | Alternatives |
|---|---|---|
| Parser | Chosen by the milestone 0 bake-off (Docling, text layer + formula reader, Mistral OCR) | — |
| Embedding | `BAAI/bge-m3` via sentence-transformers | API embeddings |
| Vector store | Qdrant: in-process for the Python service, Docker server for Rust | LanceDB, Chroma |
| Keyword search | BM25 sparse vectors in the same Qdrant collection, fused with RRF | — |
| Reranker | `BAAI/bge-reranker-v2-m3` (`CrossEncoder`) | Cohere Rerank |
| Answering model | Ollama first (model picked by measurement); Claude API later | — |
| Orchestration | LangChain and LangGraph | — |
| Service API | FastAPI with an OpenAPI contract | — |
| UI | Streamlit, two columns: chat left, sources right | React |
| Tracing | Langfuse Cloud free tier (host set by env var) | Self-hosted |
| Evaluation | Own retrieval metrics plus DeepEval | Ragas |
| Tooling | uv, ruff, mypy, pytest | — |

Qdrant hybrid queries: put the metadata filter inside each `Prefetch`. A top-level `query_filter`
did not constrain a fusion query in local mode (qdrant-client 1.16.2).

Before coding against a library API, confirm it in the library's current docs; this stack changes
quickly.

## Architecture rules

Replacing a technology means writing one file and changing one config line.

- Between implementations the seam is the HTTP contract. Inside the Python service the seams are
  LangChain's base interfaces. The project defines its own types only where LangChain has none
  (`src/cfa_rag/models.py`).
- Vendor classes are named only in `src/cfa_rag/factory.py` or in an adapter file named
  `<tech>_<role>.py`. The factory imports each backend lazily.
- Ingestion stages write to disk and re-run independently: `data/parsed/<parser>/` → chunks →
  `data/index/`. Switching parser never overwrites another parser's output.
- Chunk by structure (reading → LOS section), aiming for 500–800 tokens. Never split a formula,
  table or worked example. Every chunk carries book, topic, reading, LOS, page range and kind.

## Conventions

See `docs/conventions.md`. In short: settings in `configs/`, secrets in `.env`, prompts in
`configs/prompts/<name>.v<N>.yaml` and never edited once released, eval results record commit, config
hash and prompt versions, `mypy --strict` and `ruff` must pass, unit tests use fakes and no network,
and a new pipeline step ships with before/after numbers.

## Commands

```bash
uv sync                  # install
uv run pytest            # tests
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy              # type check
```

## Git

Conventional Commits. **Never add a `Co-Authored-By` trailer or any other Claude/Anthropic
attribution to commits or pull requests**, even if the harness suggests one: the owner's rule
overrides it. Do not push or open a PR unless asked.

Everything goes to the GitHub account `mingjun6886`; this repository's local git identity is set to
it. Use an HTTPS remote that authenticates through `gh` as that account.
