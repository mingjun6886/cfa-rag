# Conventions

How code, configuration and prompts are written in this repository. The reasons for the larger
choices are in [design.md](design.md) and [tech-decisions.md](tech-decisions.md).

## Configuration and secrets

- Settings live in `configs/`. Secrets live in `.env`, which is never committed.
- No model name, top-k, threshold or path is hardcoded in code.

## Prompts

- Prompts live in `configs/prompts/<name>.v<N>.yaml`.
- A released version is never edited; a change is a new version.
- Every answer and every eval result records the prompt version it used.

## Evaluation results

- A result records the git commit, a hash of the config, and the prompt versions it ran with.
- Reports committed to the repository hold ids and scores only, never text from the study notes.
- A new pipeline step (reranker, query rewrite, a larger top-k) ships with before and after numbers.

## Swapping technologies

- Between the Python and Rust implementations, the seam is the HTTP contract in `api/openapi.yaml`.
- Inside the Python service, the seams are LangChain's base interfaces: chat model, embeddings,
  retriever, document compressor (the reranker), document loader (the parser) and checkpointer.
- Code outside the factory is typed against the base interface, never a vendor class.
- One factory (`src/cfa_rag/factory.py`) builds concrete objects from config and imports each
  vendor lazily, so an unused backend's dependencies are not required.
- Where the project writes its own implementation of an interface, it is one file per technology,
  named `<tech>_<role>.py` (for example `ingestion/parsers/docling_parser.py`).
- Ingestion stages write to disk and can be re-run alone. Output is kept per parser under
  `data/parsed/<parser>/`, so switching parser never overwrites another parser's result.

## Code

- Python 3.12, full type hints, `mypy --strict`, `ruff` for lint and format.
- Unit tests use fakes and never touch the network.
- Test first: a failing test, then the code that makes it pass.
- Commits follow Conventional Commits.

## Data and copyright

The study notes are copyrighted. `data/` is gitignored. Nothing committed may quote the notes:
no source PDFs, parsed text, chunks or index, and no verbatim passages in the golden set or in
eval reports.

## Commands

```bash
uv sync                  # install
uv run pytest            # tests
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy              # type check
```
