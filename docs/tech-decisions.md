# Technology decisions and trade-offs

Date: 2026-11-12. Companion to [design.md](design.md).

Each section lists the options considered, what each gives and costs, and the verdict. Release
dates are from PyPI on 2026-11-12. Benchmark scores and prices come from secondary sources and are
indicative. Items marked **verified here** were checked on the owner's machine.

## Summary

| Role | Choice | Decided by | Main cost accepted |
|---|---|---|---|
| Document parser | Open: bake-off in milestone 0 | — | — |
| Chunking | By document structure, size-capped | Design default | Needs a parser that preserves headings |
| Embeddings | `bge-m3`, local | Owner | Slower than an API; about 2 GB of memory |
| Vector store | Qdrant, in-process | Owner | Its LangChain package is stale |
| Keyword search | BM25 sparse vectors in Qdrant | Owner | English-only matching |
| Reranker | `bge-reranker-v2-m3`, local | Owner | Adds latency per question |
| Answering model | Ollama now, Claude API later | Owner | Weaker citation discipline and injection resistance |
| Orchestration | LangChain + LangGraph | Owner | API churn; more abstraction than a linear flow needs |
| UI | Streamlit | Design default | Less custom look; citations are buttons, not inline links |
| Tracing | Langfuse (cloud free tier) | Owner | Traces leave the machine |
| Evaluation | DeepEval + own metrics | Owner | A local judge model is unreliable |
| Conversations | LangGraph SQLite checkpointer | Design default | One machine only |
| Injection defence | Structure and code checks, measured | Design default | No model-based input classifier |

## 1. Document parser — open

The books have a clean text layer, but every formula is an embedded image (**verified here**: text
extraction of Book 1 p.30 returns blank lines where the formulas are). The job is therefore
"formula images to LaTeX, in reading order", not full-page OCR. At 1,151 pages even a paid API
costs a few dollars once, so quality decides, not price.

| Option | Gives | Costs |
|---|---|---|
| **Docling** (MIT, released 2026-11-10) | Local; keeps structure and page numbers; formula-to-LaTeX mode; LangChain loader exists | Quality on small inline formula images is untested here |
| **Text layer + formula-image model** | Body text is exact because it is never re-recognised; only formulas go through a model | Two parts to maintain; must reinsert formulas in the right place; PyMuPDF is AGPL, so an MIT-compatible library is needed |
| **Mistral OCR** (API, about $4 per 1,000 pages) | Least setup; LaTeX output | Pages leave the machine; body text is re-recognised and can pick up errors; vendor dependency |
| PaddleOCR-VL (Apache 2.0) | Top of OmniDocBench v1.6 (96.34) | Paddle setup on macOS is awkward |
| MinerU 2.5-Pro | Second on the same benchmark (95.75); strong on formulas and tables | Heavier; sources disagree on its licence |
| Marker / Surya | Good Markdown and LaTeX | Lower benchmark score; model weights have usage restrictions |
| olmOCR 2 (Apache 2.0) | Strong on hard scans | 7B model; far more than this corpus needs |
| Tesseract | Light, CPU only | No formula or table understanding; unsuitable |

**Verdict.** Not decided. The first three run on twenty pages in milestone 0 (protocol in the
design, section 7.1). Docling is the expected default if its formulas hold up, because it is one
local tool with a permissive licence.

## 2. Chunking

| Option | Gives | Costs |
|---|---|---|
| Fixed 500–800 tokens, 100 overlap | Trivial to build | Cuts formulas, tables and worked examples in half; chunks have no natural citation |
| **By structure (reading → LOS), size-capped** | Chunks match how the notes are organised; citations name a reading and LOS | Depends on headings surviving parsing |
| Semantic chunking by embedding similarity | Adapts to topic shifts | Costly, non-deterministic, and unnecessary when headings exist |
| Parent–child (search small, return large) | Precise search with wide context | More moving parts; worth trying only if evals show context is too thin |

**Verdict.** By structure. The corpus has about 684 LOS headings to split on (**verified here**).
Chunk size is a tuning parameter decided by retrieval metrics.

## 3. Embeddings

| Option | Gives | Costs |
|---|---|---|
| **`bge-m3`, local** | Free; multilingual, so Vietnamese questions match English text; nothing leaves the machine | About 2 GB of memory; slower indexing than an API |
| API embeddings (OpenAI, Voyage, Cohere) | Fast; no local memory; finance-tuned models exist | Cost per run; text sent to a vendor; CI needs a secret |
| Small local model | Light and fast | Weaker cross-language matching |

**Verdict.** `bge-m3`. Revisit only if retrieval metrics plateau.

## 4. Vector store

| Option | Gives | Costs |
|---|---|---|
| **Qdrant** (client 1.20.0, 2026-10-22) | Dense + sparse + RRF in one query; same API in-process, in Docker and hosted; metadata filters | `langchain-qdrant` last released 2025-10-22; a filter must sit inside each prefetch |
| Chroma (1.5.9, 2026-05-05) | Simplest start | Hybrid search in the local open-source build is unclear; the company is joining Replit and its cloud is closing |
| Weaviate | Mature hybrid search | Needs a server process |
| LanceDB | Embedded; built-in full-text and hybrid | Less common in job postings |
| pgvector | One database for everything | Needs Postgres; keyword ranking is not true BM25 without an extension |

**Verified here:** in-process Qdrant ran a dense + sparse query fused with RRF (qdrant-client
1.16.2). A top-level filter did not constrain the fused query; the filter belongs in each prefetch.

**Verdict.** Qdrant. If its LangChain package cannot do hybrid search in-process, the project
writes a small retriever over the Qdrant client.

## 5. Keyword search

| Option | Gives | Costs |
|---|---|---|
| **BM25 sparse vectors in the same Qdrant collection** | One store, one query, nothing to keep in sync | Sparse vectors must be generated at index and query time |
| Separate in-memory BM25 index | Easy to prototype | Two indexes that can drift apart; rebuilt on every start |
| Dense only | Simplest | Misses exact terms, formula names and ticker-like tokens |

**Verdict.** Sparse vectors in Qdrant, fused by rank (RRF) and not by raw score. BM25 cannot match
a Vietnamese question to English text, which is why the question is rewritten into English first.

## 6. Reranker

| Option | Gives | Costs |
|---|---|---|
| **`bge-reranker-v2-m3`, local** | Free; multilingual; its top score doubles as the grounding gate | Extra latency per question; about 2 GB of memory |
| Cohere Rerank (API) | Strong; no local memory | Cost; vendor; text leaves the machine |
| None | Fastest | Lower precision in the five chunks the model sees |

**Verdict.** Local cross-encoder, kept only if it improves hit@5 and answer metrics over
hybrid search alone.

## 7. Answering model

| Option | Gives | Costs |
|---|---|---|
| **Local via Ollama** | Free; private; works offline | Smaller models follow citation rules less reliably and are easier to manipulate; no model in GitHub CI |
| Claude API | Stronger answers; native Citations that return the quoted span and its location | Cost; an API key; text sent to a vendor |

The machine currently has only `llama3.2` (2 GB), which is too small for this task. Candidates to
measure, from 2026 guides for 24 GB Macs: Qwen3 14B, Gemma 4 12B, Qwen3.5 9B. The embedding model
and reranker also need memory, so the budget for the answering model is about 10 GB.

**Verdict.** Ollama first, model picked by measurement on the golden set. The answer contract
(statements with chunk ids and quotes) is the same for both, so adding Claude later is one new
adapter. Claude's Citations cannot be combined with structured output, so that adapter maps
citation blocks onto the same answer type.

## 8. Orchestration

| Option | Gives | Costs |
|---|---|---|
| **LangChain + LangGraph** (1.5.0, 2026-11-11; LangGraph 1.2.20) | Widely used and asked for; ready interfaces for every swap point; graph with branches, retries and persistence; Langfuse integration | Frequent API changes; integrations age unevenly (see Qdrant); more indirection when debugging |
| Plain Python | Nothing hidden; fewest dependencies | The project must write its own interfaces, persistence and tracing hooks |
| LlamaIndex | Strong retrieval building blocks | A second large framework for the same job |

**Verdict.** LangChain and LangGraph from the start, by owner decision. To limit the cost: versions
are pinned, vendor classes are named only in one factory, and the question flow is an explicit
LangGraph graph, not a chain of opaque helpers.

## 9. Chat UI

| Option | Gives | Costs |
|---|---|---|
| **Streamlit** (1.67.0, 2026-11-05) | Python only; chat, columns and sidebar built in; actively released | Looks like a data app; citations are buttons under the answer; reruns the script on each interaction |
| Chainlit (2.12.0, 2026-08-25) | Built for chat; side panel for sources; history | Slower release pace; history needs an auth and data layer |
| Gradio (6.31.0, 2026-10-28) | Quick chat component | Two-column source view takes more custom work |
| React + FastAPI | Full control; inline citations; shows API design | A second toolchain and much more code |

**Verdict.** Streamlit. The UI calls one function of the core, so a React frontend can replace it
later without touching retrieval.

## 10. Tracing

| Option | Gives | Costs |
|---|---|---|
| **Langfuse** (SDK 5.2.0, 2026-11-05) | Open source; traces, sessions, scores, datasets; LangChain callback | Another service to run or sign up for |
| LangSmith | Tightest LangChain integration | Closed source; hosted only on the free tier |
| Arize Phoenix | Open source; OpenTelemetry-based | Sessions and prompt tooling are less central |

| Hosting | Gives | Costs |
|---|---|---|
| **Langfuse Cloud, free tier** (50k units a month, 30 days of data, per its pricing page) | Nothing to run locally | Traces, which contain passages from the notes, are stored by a vendor in a private project |
| Self-hosted with Docker | Everything stays on the machine | Several containers competing for memory with the local model |

**Verdict.** Langfuse on the cloud free tier, by owner decision, with the host set by an
environment variable so that moving to self-hosting is a config change. Prompts stay in versioned
files in git; Langfuse records which version each trace used.

## 11. Evaluation

| Option | Gives | Costs |
|---|---|---|
| **DeepEval** (4.3.4, 2026-11-11) + own metrics | pytest-native, so a failing metric fails CI; actively released; supports a local Ollama judge | Judge-based metrics are only as good as the judge |
| Ragas (0.4.3, 2026-01-13) | The best-known RAG metric names | No release in ten months |
| Own metrics only | Deterministic and free | Cannot judge whether a quote actually supports a statement |

**Verdict.** Deterministic metrics gate CI: hit@k, MRR, citation-check pass rate, refusal accuracy
and attack success rate. DeepEval adds faithfulness and correctness. With a local judge those two
are reported but do not gate until the judge agrees with hand labels.

## 12. Conversation storage

| Option | Gives | Costs |
|---|---|---|
| **LangGraph SQLite checkpointer + a small list table** | Built-in persistence by thread id; one local file | Single machine, single user |
| Own tables for sessions and messages | Full control of the schema | Rebuilds what LangGraph already provides |
| Postgres | Multi-user ready | A server for a one-user app |

**Verdict.** SQLite checkpointer. The thread id is also the Langfuse session id.

## 13. Prompt-injection defence

| Option | Gives | Costs |
|---|---|---|
| Instructions in the prompt only | No extra code | A prompt cannot enforce anything; fails silently |
| Model-based input classifier | Catches some known attack phrasing | Extra call and latency; itself attackable; false positives on honest questions |
| **Structure and code checks, measured** | Limits what an attack can achieve whatever the model was told; a number to report | Does not stop a quote being misused to "support" an unrelated statement |

**Verdict.** No tools, no secrets, data separated from instructions, a grounding gate, a citation
check in code, and safe rendering. An attack set with deterministic success tests reports the
attack success rate. A classifier is added only if that number shows it is needed.

## 14. Continuous integration

| Option | Gives | Costs |
|---|---|---|
| Full evals on every PR | The original goal | GitHub runners have no notes and no local model; judge-based scores are slow and noisy |
| **Deterministic gate in CI; full run locally with a committed report** | Stable, free, honest about what CI can know | The model-judged part depends on the owner running it |
| Add model-judged evals in CI later | Closes the gap | Needs an API key as a repository secret |

**Verdict.** The middle option now, the third once the Claude API is added. CI uses a small openly
licensed sample corpus so that it, and any visitor, can run the pipeline.

## Sources

- [Best Open-Source OCR Models in 2026, Ranked by Benchmark (Roboflow)](https://blog.roboflow.com/best-open-source-ocr-models/)
- [MinerU2.5-Pro (arXiv)](https://arxiv.org/pdf/2604.04771)
- [Mistral OCR 4 vs top document parsing APIs (Eden AI)](https://www.edenai.co/post/mistral-ocr-4-vs-top-document-parsing-apis-features-benchmarks-and-integration-guide)
- [Qdrant: Hybrid and Multi-Stage Queries](https://qdrant.tech/documentation/hybrid-queries/)
- [Qdrant: Chroma hybrid retrieval migration](https://qdrant.tech/documentation/tutorials-operations/chroma-hybrid-retrieval-migration/index.md)
- [Chroma joins Replit (Runtime Wire)](https://runtimewire.com/article/chroma-joins-replit-agent-context)
- [Langfuse pricing](https://langfuse.com/pricing)
- [RAG evaluation tools 2026: Ragas vs DeepEval vs Braintrust vs Giskard](https://ecorpit.com/rag-evaluation-tools-ragas-deepeval-braintrust-giskard-2026/)
- [LLM Evaluation Made Easy: Using DeepEval and Ollama](https://blog.gopenai.com/llm-evaluation-made-easy-using-deepeval-and-ollama-for-qa-metrics-ec92fa6e99ee)
- [Best Local LLM on Mac Mini M4 Pro (24 GB)](https://bestllmfor.com/best/mac-mini-m4-pro/)
- [OpenStax Principles of Finance, preface](https://openstax.org/books/principles-finance/pages/preface)
