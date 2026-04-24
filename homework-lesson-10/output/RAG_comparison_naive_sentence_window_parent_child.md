# Comparing RAG Chunking Strategies: Naive (Whole-Document), Sentence-Window (Sliding-Window), and Parent–Child (Hierarchical)

## Summary Table

| Approach | Typical Precision | Typical Recall | Index Size | Engineering Complexity | Typical end-to-end p95 latency (Small / Medium / Large) |
|---|---:|---:|---:|---|---:|
| Naive (Whole-Document) | Low→Moderate (for long docs) | Moderate | Small (1 vector/doc) | Low | 300–800 ms / 500–1500 ms / 800–2500 ms |
| Sentence-Window (Sliding-Window) | Moderate→High | High (better recall on long docs) | Large (many overlapping chunks) | Medium | 300–900 ms / 600–1800 ms / 1000–3000 ms |
| Parent–Child (Hierarchical) | High (best for provenance/coherence) | High | Large (parents + children) | High | 250–800 ms / 550–1400 ms / 900–2600 ms |

Notes: latency ranges are illustrative p95 ranges under representative configurations (see Latency Benchmarks section and assumptions below). Real-world numbers depend on embedding model, ANN index, reranker, reader model size, hardware (CPU vs GPU), batching, and network overhead.

---

## Executive Summary

This report compares three retrieval-augmentation chunking/retrieval strategies used with modern retriever–reader and retrieval-augmented generation (RAG) systems:
- Naive / whole-document retrieval
- Sentence-window / sliding-window chunking (passage-level with overlap)
- Parent–child / hierarchical chunking (children = fine-grained passages; parents = section-level context or summaries)

Concise recommendation:
- Short, self-contained docs: Naive (whole-document) indexing is simplest.
- General long-doc corpora: Sliding-window chunking with overlap is a robust default.
- Structured, provenance-sensitive applications: Parent–child hierarchical chunking gives the best precision/coherence trade-off; accept extra engineering cost.

---

## Findings (abridged)

[Omitted here for brevity — full report includes definitions, literature (RAG, DPR, FiD, ColBERT, ANCE, Contriever), embedding guidance, architecture patterns, hyperparameters, vector-store engineering, security/compliance, parent–child pseudocode & scoring, cost examples, evaluation protocol, and multilingual/domain guidance.]

---

## Latency Benchmarks (Illustrative)

This section provides component-level and end-to-end p95 latency examples for typical pipelines and corpus scales. These are engineering approximations for planning and should be validated on your hardware and chosen models.

Assumptions (typical setups used to produce ranges):
- Embedding: local model or managed API — query embed time ~ 10–200 ms depending on model and remote vs local.
- ANN search:
  - HNSW in-memory (small/medium): 5–80 ms
  - IVF+PQ or distributed (large): 100–300 ms
- Cross-encoder reranker (CPU): 50–300 ms for reranking top 50–100 items; on GPU this may drop to 10–80 ms.
- FiD / generative reader (GPU) tokenized input size drives latency. Example: decoding on a moderate GPU for 1k–4k prompt tokens + ~150 tokens output → 200–1500 ms depending on model size (T5-base → T5-large → proprietary LLMs differ).
- Network overhead and orchestration: add 5–50 ms depending on topology.

Component-level illustrative p95 latency ranges (single-request, no batching):
- Query embedding: 10–200 ms
- ANN search (HNSW, small index): 5–20 ms
- ANN search (HNSW, medium): 20–80 ms
- ANN search (IVF+PQ distributed): 100–300 ms
- Cross-encoder rerank (top 100 → top 20) CPU: 100–350 ms; GPU: 10–80 ms
- FiD generative read (consume 10–20 passages → prompt 1k–3k tokens): 200–1,500 ms

End-to-end p95 illustrative numbers by approach and corpus size
- Small corpus (<= 100k vectors, in-memory HNSW; FiD on single GPU)
  - Naive: 300–800 ms (embed q 10–50 ms; ANN 5–20 ms; LLM generation 200–700 ms)
  - Sliding-window: 300–900 ms (embed 10–50 ms; ANN 5–30 ms; reranker 50–150 ms; FiD 200–700 ms)
  - Parent–Child: 250–800 ms (embed 10–50 ms; ANN 5–30 ms; parent-score calc negligible; reranker 50–150 ms; FiD 200–700 ms)

- Medium corpus (~1M–10M vectors; HNSW or HNSW+PQ; FiD on GPU)
  - Naive: 500–1500 ms (ANN 20–80 ms; LLM generation larger due to doc context)
  - Sliding-window: 600–1800 ms (ANN 20–80 ms; reranker 100–300 ms; FiD 400–900 ms)
  - Parent–Child: 550–1400 ms (ANN 20–80 ms; parent sim + rerank 100–300 ms; FiD 300–800 ms)

- Large corpus (tens of millions; IVF+PQ distributed; multi-node ANN; reranker on CPU/GPU)
  - Naive: 800–2500 ms (ANN 100–300 ms; LLM generation 600–1500 ms)
  - Sliding-window: 1000–3000 ms (ANN 100–300 ms; reranker 150–500 ms; FiD 600–1500 ms)
  - Parent–Child: 900–2600 ms (ANN 100–300 ms; parent-score + rerank 150–500 ms; FiD 500–1300 ms)

Caveats and how to reduce latency
- Batching: amortize embedding and LLM costs by batching similar queries; increases throughput but may add tail latency for single requests.
- Smaller readers or distilled models: reduce FiD generation latency at possible cost to answer quality.
- Reduce FiD passages: improve reranker to feed fewer, higher-quality passages (e.g., top 5–10) to the reader.
- Use GPU-accelerated rerankers and readers; colocate ANN nodes and rerankers to reduce network overhead.
- Use efficient encoders and quantization to speed ANN search.

---

If you'd like, I will:
- run a small latency micro-benchmark harness (code scaffold) for your target stack (FAISS/Milvus + embedding model + reranker + FiD) and produce measured p50/p95/p99 numbers; or
- produce a compact table of component-level latency expectations for specific hardware (CPU-only, single-GPU, multi-GPU), or
- embed these latency ranges into the main report sections where each approach is described in detail.

Would you like measured micro-benchmarks (I can provide code to run locally or on a cloud instance)?
