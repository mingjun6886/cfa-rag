# CFA RAG — Design

Date: 2026-11-12 · Status: approved by the owner on 2026-11-12; amended the same day to add the
HTTP API and the Rust implementation (sections 7.8 and 7.9)

The reasoning behind each technology choice is in [tech-decisions.md](tech-decisions.md).

## 1. Intent

A chat application that answers questions about CFA Level I material from a set of study notes.
It cites the passage behind every statement and says so plainly when the notes do not support an
answer.

It is a public portfolio project for AI engineering roles. Someone who spends a few minutes on the
repository should see how a retrieval system is built, measured and defended, and not only that a
chatbot runs.

The question-serving path is built twice behind one HTTP contract: first in Python, then again in
Rust. One eval harness judges both. The owner wants a Rust project, and a known-good reference to
learn the language against.

There is no deadline, and the owner may show the repository to an employer at any time. So every
milestone must leave the public repository runnable and presentable.

## 2. Goals

1. A chat UI: conversation on the left, source panel on the right. Selecting a citation shows the
   cited passage with its book, reading and page.
2. Every statement in an answer carries a citation that code has checked against the retrieved
   text. An answer that fails the check is not shown; the app declines.
3. Conversations are saved, follow-up questions are understood in context, and a past conversation
   can be reopened from a list.
4. Questions may be in Vietnamese or English. The corpus is English. The answer is in the language
   of the question; quoted source text stays in English.
5. Every step of a question is traced in Langfuse, and a conversation is one Langfuse session.
6. Quality is measured: retrieval, faithfulness and correctness of answers, refusal behaviour, and
   resistance to prompt injection. A change that lowers a gated number fails CI.
7. Replacing a technology means writing one file and changing one config line.
8. A visitor without the study notes can run the whole system on a small sample corpus.
9. The repository explains itself: README, this design, the trade-off record, and an interactive
   page that walks through the three flows. The page is a static HTML file under `docs/`, served
   by GitHub Pages; the README carries a static diagram of the same flows.
10. The question flow is served over an HTTP API. The UI and the eval harness are clients of that
    API and work unchanged against either implementation.

## 3. Non-goals

- Login, multiple users, or hosting the app on a public server.
- Ingesting Markdown or web pages. Only PDF is in scope.
- A calculator tool. The app explains formulas and worked examples from the notes; it does not
  promise correct arithmetic on new numbers.
- CFA Level II or III.
- A phone layout.
- A React frontend, the Claude API, and thumbs-up/down feedback. These are in the last milestone.
- Rewriting ingestion, evaluation or the UI in Rust. Only the question-serving path is built twice.

## 4. Anti-goals

These would make the project a failure even if it works.

- **Publishing copyrighted text.** No source PDFs, parsed text, chunks, index, or verbatim passages
  from the notes in the repository, in committed eval reports, or in a public demo.
- **Claims without numbers.** The README never says "accurate" or "secure" without the measurement
  next to it, including the unflattering ones.
- **A separate path for evaluation.** Evals call the same HTTP API the UI calls.
- **A Rust port that only looks similar.** It is done when it passes the same contract tests and
  its gated metrics are within tolerance of the Python service's, not before.
- **Refusing to look good.** A system that declines everything scores perfectly on faithfulness.
  False refusals are measured and gated.
- **Prompts hidden in code.** Every prompt is a versioned file.

## 5. Constraints

- **Machine:** Apple M4 Pro, 24 GB. Models run locally through Ollama. Docker is available.
- **Corpus:** SchweserNotes 2024 Level I, five books and the QuickSheet, 1,151 pages. The PDFs have
  a clean text layer, but **formulas are embedded images** that plain text extraction drops. The
  text has about 684 `LOS x.y` headings and 232 `MODULE QUIZ` markers.
- **Copyright:** the notes stay on the owner's machine under `data/`, which is gitignored.
- **GitHub:** public repository under the account `mingjun6886`. Commits carry no attribution
  trailers. SSH on this machine authenticates as a different account, so the remote uses HTTPS.
- **Tools:** current and widely used, since the project is also a record of the owner's skills.
- **Cost:** local and free first. Paid APIs come later.
- **Speed:** no latency target is set. Time per step is measured in traces and reported.

## 6. Decisions

### Decided by the owner

| Area | Decision |
|---|---|
| Orchestration | LangChain and LangGraph from the first milestone |
| Answering model | Local through Ollama first; Claude API later |
| Vector store | Qdrant |
| Embeddings | `BAAI/bge-m3`, local |
| Reranker | `BAAI/bge-reranker-v2-m3`, local |
| Evaluation | DeepEval, plus the project's own retrieval metrics |
| Tracing | Langfuse |
| UI layout | Two columns: chat left, sources right |
| Conversations | Saved, context-aware follow-ups, reopenable from a list; one user, no login, stored locally |
| Safety | Defence against prompt injection, with measured results |
| Repository | Public, named `cfa-rag`, under `mingjun6886` |
| Implementations | Python first; then the question-serving path again in Rust, behind the same HTTP API and judged by the same eval harness |
| Langfuse hosting | Langfuse Cloud free tier; the host is an env var, so self-hosting stays a config change |
| Golden set | Public, on condition that every item is in the owner's own words, with page references and no text copied from the notes or their quizzes |

### Defaults chosen during design, not yet confirmed

The owner delegated the UI technology. The rest are proposals; each can be overturned.

| Area | Default | Why |
|---|---|---|
| UI technology | Streamlit | Python only, no frontend toolchain; it is a client of the HTTP API |
| Service API | FastAPI for the Python service; the contract is an OpenAPI file in the repository | Both implementations and both clients are tested against one written contract |
| Rust code location | A `rust/` directory in this repository | One README shows both implementations and one set of numbers |
| Qdrant mode | In-process for the Python service; a Qdrant server in Docker from the Rust milestone on | In-process mode exists only in the Python client; until then it means no setup for visitors or CI |
| Rust design | Written as its own design when milestone 4 starts | Crate choices made now would be stale; this document fixes only the boundary |
| Swap seams | LangChain's own base interfaces | LangChain already defines them; a second layer would duplicate it |
| Conversation storage | LangGraph SQLite checkpointer, plus a small table for the list | Built-in persistence keyed by thread id |
| Citation format | Each statement lists chunk ids and a verbatim quote, checked by code | Works with any model; maps onto Claude's Citations later |
| Input guard | Deterministic limits only, no model-based classifier | The code checks after generation carry the weight; add a classifier only if the attack set shows the need |
| Sample corpus | Chapters from OpenStax *Principles of Finance*, first edition (CC BY 4.0) | Openly licensed finance text; licence to be re-checked on the book page before committing |
| CI gate | Deterministic metrics gate every PR; model-judged metrics run locally until an API model is available | GitHub's runners have neither the notes nor a local model |
| Local model | Chosen by measurement among two or three candidates that fit in about 10 GB | No ranking found online is as reliable as a short local test |
| Documentation language | English | Public portfolio |
| Licence | MIT | Common default; constrains which dependencies are acceptable (see parser) |

### Not decided

- **Document parser.** Chosen by the bake-off in milestone 0 (section 7.1).

## 7. System

Three flows. The question flow sits behind an HTTP API (section 7.8). In the Python service
LangGraph runs it; Langfuse records it.

### 7.1 Ingestion (offline)

`PDF → parse → chunk → embed → index`. Each stage writes to disk and can be re-run alone.

- **Parse.** Take body text from the PDF text layer, convert formula images to LaTeX in reading
  order, and keep the page number of everything. Output goes to `data/parsed/<parser>/`, so trying
  another parser never overwrites an earlier result.
- **Parser bake-off.** Twenty pages across the five books: eight formula-heavy, six table-heavy,
  six plain. Candidates: Docling with formula enrichment; text layer plus a model that reads only
  the formula images; Mistral OCR. Judged on formula exactness (hand-checked against about forty
  formulas), reading order, table fidelity, page numbers, runtime, cost and licence. Parsed pages
  stay under `data/`; only the score table is committed.
- **Chunk.** Split by reading, then by LOS section, aiming for 500–800 tokens. Never split a
  formula, a table or a worked example. Overlap applies only where a long section is split by
  size. Each chunk carries: book, topic, reading, LOS, page range, and kind (text, example, quiz,
  answer key). Quiz and answer-key chunks are left out of the index, so an answer key cannot
  masquerade as an explanation.
- **Embed and index.** One Qdrant collection holds a dense vector (`bge-m3`) and a BM25 sparse
  vector per chunk. Qdrant runs in-process from `data/index/`.

### 7.2 Question flow (per question)

| # | Step | Behaviour | Can stop? |
|---|---|---|---|
| 1 | Input check | Strip control characters; reject empty input and input over 2,000 characters | Yes: `input_rejected` |
| 2 | Rewrite | A model turns the question plus the last few turns into one standalone English question, and reports the language the user wrote in | No |
| 3 | Hybrid search | Dense and BM25 searches in Qdrant, fused with RRF; 20 chunks | No |
| 4 | Rerank | Cross-encoder scores each chunk against the question; keep 5 | No |
| 5 | Grounding gate | If the top score is under the threshold, decline without calling the answering model | Yes: `no_support` |
| 6 | Answer | A model writes the answer from the 5 chunks only, as structured output | No |
| 7 | Citation check | Code verifies the answer (rules below). On failure, regenerate once with the reasons, then decline | Yes: `verification_failed` |
| 8 | Respond | Show the answer and its sources; save the turn | — |

Rules the builder must keep:

- **Only the rewrite step sees conversation history.** The answering step receives the standalone
  question, the language to answer in, and the chunks. This keeps the answer prompt small and removes history as a way to
  smuggle instructions into it.
- **Answer contract.** The answering model returns a list of statements. Each statement has text
  and one or more citations; a citation is a chunk id and a verbatim quote from that chunk.
- **Citation check.** A statement passes when it has at least one citation, the chunk id is among
  the five chunks given, and the quote occurs in that chunk after normalising whitespace and case.
  A quote must be long enough to be meaningful (a minimum the builder sets and tests).
- **A refusal is a normal result**, with a reason code from the table and a plain sentence for the
  user. It is traced and counted like an answer.
- **Thresholds are calibrated** on one part of the golden set and reported on the rest. They live
  in config, as do the counts in the table (20 and 5 are starting values).
- **The quote check proves the quote exists, not that it supports the statement.** That gap is
  what the model-judged faithfulness metric measures, and the README says so.

### 7.3 Conversations

- A conversation has an id, which is also the Langfuse session id. In the Python service it is a
  LangGraph thread.
- State is saved by the SQLite checkpointer in `data/app.db`. A small table holds what the sidebar
  needs: id, title (from the first question), created and updated times.
- The sidebar lists conversations newest first, with "new conversation" and "delete".
- The rewrite step receives the last six turns (configurable).

### 7.4 Chat UI

Streamlit. Sidebar: conversation list. Main area, two columns: the chat, and a source panel.
Citations are numbered buttons under each answer; selecting one shows that passage, with book,
reading and page, in the source panel. A refusal is shown as a distinct, calm message. The UI is a
client of the HTTP API (section 7.8) and holds no retrieval logic.

An answer appears only after the citation check, so it is not streamed word by word. While the
question is processed, the UI shows which step is in progress, from the API's step events.

Model output is rendered as plain Markdown with raw HTML off, and images and links are removed
before display.

### 7.5 Prompt-injection defence

**What an attacker can gain.** The app has one user, no tools and no secrets; the prompts are
public. The realistic harms are: an ungrounded or off-topic answer presented as grounded, the
system used as a general chatbot, and hostile Markdown in the output.

**Layers.**

1. Input limits (step 1).
2. Data kept apart from instructions: the question, the history and each chunk go into the prompt
   in labelled blocks, and the system prompt states that their content is data.
3. Grounding gate (step 5): off-topic requests retrieve nothing relevant and stop there.
4. Citation check (step 7): code, not a prompt, decides whether an answer is shown.
5. Safe rendering (7.4).

**Measurement.** An attack set runs through the same HTTP API. Each case has a deterministic success
test, for example a canary string the attack tries to make the app print, a sentence of the system
prompt it tries to extract, or an off-topic task it tries to get done. A separate case plants an
instruction inside a retrieved chunk, to cover the day web pages are ingested. The reported number
is the attack success rate. No layer is claimed to be complete, and small local models are expected
to do worse than large ones; the numbers are published either way.

### 7.6 Tracing

A Langfuse callback is attached where the graph is invoked, so each step is a span. Each trace
records the conversation id, prompt versions, a hash of the config, the git commit, the top rerank
score, the citation-check result and any refusal reason. Tracing is optional: with the Langfuse
variables unset the app runs without it. Traces contain passages from the notes, so the Langfuse
project stays private.

### 7.7 Evaluation

**Datasets**, each with a counterpart for the sample corpus:

- answerable questions with a reference answer and the pages that support it, about a quarter of
  them in Vietnamese;
- unanswerable questions (outside the notes, or outside Level I);
- attack cases.

**Metrics.**

| Metric | Needs a judge model? | Gates CI? |
|---|---|---|
| Retrieval hit@5 and MRR@10 | No | Yes |
| Citation-check pass rate | No | Yes |
| Refusal accuracy: declines the unanswerable, answers the answerable | No | Yes |
| Attack success rate | No | Yes |
| Faithfulness (DeepEval) | Yes | Not until the judge is validated |
| Answer correctness against the reference (DeepEval) | Yes | Not until the judge is validated |

- **One harness, any implementation.** The harness takes a base URL and computes every metric from
  API responses, including retrieval metrics from the `retrieved` list in each result.
- **Golden questions** may be drafted with a model's help, but each one is checked by the owner
  against the notes before it counts.
- **Gates** are the recorded baseline minus a tolerance, stored in `evals/thresholds.yaml`.
- **Judge.** The first judge is a local model, which is weak and partly grades its own family. Its
  scores are reported but do not gate until they agree with twenty hand labels, or until the judge
  moves to an API model.
- **Every result** records the git commit, config hash and prompt versions, and is sent to Langfuse.
- **Reports** committed to the repository hold ids and scores only, never text from the notes.

**CI on GitHub.** Lint, type check and unit tests; retrieval metrics on the sample corpus (parsed
sample chunks are committed, and the embedding model is cached); and tests of the input check,
citation check and renderer driven by a scripted fake model. The full run against the notes with a
real model happens on the owner's machine and its report is committed.

### 7.8 Service API

The question flow is reached only through this API. The contract is an OpenAPI file at
`api/openapi.yaml`. Contract tests take a base URL and must pass against every implementation.

| Method and path | Purpose |
|---|---|
| `GET /health` | Liveness, with the implementation's name and version |
| `POST /conversations` | Create a conversation; returns its id |
| `GET /conversations` | List conversations, newest first |
| `GET /conversations/{id}` | A conversation's turns |
| `DELETE /conversations/{id}` | Delete it |
| `POST /conversations/{id}/messages` | Ask a question; returns a stream of server-sent events |

The message stream carries a `step` event as each step of section 7.2 starts, then one `result`
event, and closes. A result is an answer or a refusal:

- **Answer:** the statements with their citations, the five source chunks (id, book, reading, LOS,
  page range, text), and the language answered in.
- **Refusal:** the reason code and the sentence shown to the user.
- **Both:** the trace id, and `retrieved`: the ranked chunks from search and rerank, as ids with
  book, page range and score. The eval harness computes retrieval metrics from this list, so
  evaluation has no code path of its own.

The API listens on localhost only and has no authentication, in line with the one-user non-goal.

### 7.9 Rust implementation of the serving path

**Built in Rust:** the API server, conversation storage, and steps 1–8 of the question flow,
including tracing.

**Shared, not rebuilt:** ingestion and the index it produces, the versioned prompt files, the
config values, the eval harness and golden sets, and the Streamlit UI.

**Done means:** the contract tests pass against the Rust service; every gated metric is within
tolerance of the Python service's on the same golden set; and the README reports quality, latency
(p50 and p95 per step) and memory for both, side by side.

**Risks to settle in the Rust design:**

- Query-time vectors must be produced exactly as at index time. Dense: the same `bge-m3` weights
  in another runtime give slightly different numbers, so thresholds may need their own
  calibration. Sparse: tokenisation must match; having the Qdrant server compute BM25 for both
  services is the likely answer.
- Langfuse has no official Rust SDK. Traces would go through OpenTelemetry; this is unverified.
- The most used Rust LLM framework, `rig-core`, is pre-1.0. Whether to use it or write the eight
  steps directly is decided then.

## 8. Swappability

Between implementations, the seam is the HTTP contract (section 7.8). Inside the Python service,
LangChain's base interfaces are the seams: chat model, embeddings, retriever, document compressor
(the reranker), document loader (the parser) and checkpointer.

- Code outside the factory is typed against the base interface, never a vendor class.
- One factory builds the concrete objects from config and imports each vendor lazily.
- Where the project writes its own implementation of an interface, it is one file per technology,
  named `<tech>_<role>.py`.
- The project defines its own types only where LangChain has none: answer, statement, citation,
  refusal.
- Conventions for config, prompts and tests are recorded in `docs/conventions.md`, written in
  milestone 0.

**Known risk.** The `langchain-qdrant` package was last released on 2025-10-22. Milestone 1 starts
by confirming it does hybrid search against an in-process Qdrant. If it does not, the retriever is
a small project-owned class over `qdrant-client`, where this was confirmed working. In that client,
a metadata filter must be placed inside each prefetch.

## 9. Milestones

Each one ends with the README updated and the public repository runnable.

| # | Name | Contents | Done when |
|---|---|---|---|
| 0 | Public foundation | README, this design, trade-off record, conventions page, interactive flow page; parser bake-off and decision; sample corpus; 25–30 golden questions; retrieval metric script | The repository is public and a parser is chosen on evidence |
| 1 | Walking skeleton | Ingestion; dense retrieval; structured answer with citation check; LangGraph; Ollama; the HTTP API and its OpenAPI contract; Streamlit two-column UI as a client; Langfuse tracing; versioned prompts | A question gets a cited answer in the UI, with a trace; baseline numbers are in the README |
| 2 | Retrieval quality and conversations | Hybrid search, rerank, calibrated grounding gate, rewrite for follow-ups and Vietnamese, conversation list | Each addition is kept only if it beats the baseline, with numbers recorded |
| 3 | Evals and safety in CI | 100–200 golden questions, unanswerable set, attack set, DeepEval metrics, thresholds, contract tests, an eval harness that takes a base URL, GitHub Actions gate | A PR that lowers a gated metric fails |
| 4 | Rust serving path | Its own design first; then the API server and question flow in `rust/`, reading the same index and prompts | Contract tests pass, gated metrics are within tolerance of the Python service, and the README compares both |
| 5 | Later | Claude API for answering (Citations) and judging, model-judged evals in CI, React UI, other loaders, calculator tool, feedback buttons | — |

## 10. Left to the builder

- Module layout inside `src/cfa_rag/`, within the rules of section 8.
- Event names and field names in the OpenAPI contract, within section 7.8.
- Prompt wording, the structured-output schema details, and the minimum quote length.
- The chunker's handling of edge cases, and how tables are represented.
- Which local model, by measurement on the golden set.
- Threshold values and tolerances.
- Streamlit component choices, and how the embedding model is cached in CI.
- Text-layer library if that parser route wins: it must be compatible with an MIT repository
  (PyMuPDF is AGPL).
