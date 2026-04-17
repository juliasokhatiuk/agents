prepared by Yulia Sokhatyuk

# Comprehensive RAG Comparison & Engineering Guide

## Title
Comprehensive Comparison: Naïve, Sentence-Window, and Parent–Child RAG — Evaluation, Engineering, Costs, Ops, and Governance

## Executive Summary
This document compares three Retrieval-Augmented Generation (RAG) approaches — Naïve, Sentence-Window, and Parent–Child — and provides a practical, reproducible engineering playbook for building, evaluating, and operating RAG systems. It includes definitions, retrieval and prompt-assembly workflows, concrete hyperparameters and heuristics, a reproducible evaluation protocol, index-technology tuning, reranking and embedding recommendations, cost-estimation formulas with a worked example, operational runbooks (sharding, reindexing, backups), dedup/merge heuristics, hallucination detection and mitigation strategies, and prescriptive governance controls (PII redaction, IAM, retention/GDPR). Appendices contain runnable pseudocode and parameter grids for experiments.

Key recommendations (short):
- Start with bi-encoder retrieval + HNSW for dev; retrieve K=100 candidates, cross-rerank top_n=16–32.
- For short factual queries use Sentence-Window; for long structured docs use Parent–Child (parent-first or child-first depending on use-case).
- Default hyperparameters: child=100–300 tokens, parent≈800–1,500 tokens, overlap=50–100 tokens, final top_k to LLM=3–8.
- Implement dedup by embedding cosine ≥0.92 and/or token Jaccard ≥0.6; merge adjacent spans with gap ≤50 tokens.
- Evaluate retrieval (Recall@k, MRR, nDCG), generation (EM/F1, ROUGE, BERTScore) and faithfulness (QAGS/FEQA/FactCC) plus human evaluation for hallucination.
- Budget and ops: use IVF+PQ for very large corpora (100M+ vectors), HNSW for up to ~10M vectors in memory; warm/cold tiers and caching are essential.


## Findings (Definitions, how they work, and quick pros/cons)

1) Naïve RAG
- Definition: Chunk documents into fixed-size blocks (e.g., 400–800 tokens). Store embeddings per chunk. Query → nearest neighbor search → concat top_k chunks → LLM.
- Retrieval: single-level dense retrieve (bi-encoder) optionally combined with BM25 filtering.
- Prompt assembly: concatenated chunks until token budget.
- Pros: simple, low engineering effort; good for corpora where answers are localized.
- Cons: noisy context mixing, higher hallucination risk, poor for long/structured docs.

2) Sentence-Window RAG
- Definition: Index sentence-level (or short-window) units (sentence ± N sentences/tokens). Retrieve windows that center on relevant sentences to improve precision.
- Retrieval: semantic retrieval on windows; merge overlapping windows; rerank top candidates.
- Prompt assembly: merged windows with provenance headers.
- Pros: high precision for sentence-level facts; smaller prompt size; lower irrelevant noise.
- Cons: may lose broader context; larger index (one entry per window); needs intelligent merge.

3) Parent–Child (Hierarchical) RAG
- Definition: Maintain two granularities: children (fine-grained chunks ~100–300 tokens) and parents (sections/docs ~800–2000 tokens). Two-stage retrieval (parent-first or child-first) combines micro and macro context.
- Retrieval: either retrieve parents then children (parent-first) or children then map to parents (child-first). Reranking and parent summaries help.
- Prompt assembly: selected children + optional parent excerpts or summaries.
- Pros: best for long documents and complex queries that need both detail and context; improves provenance.
- Cons: more engineering complexity, larger storage and potential latency for extra lookups.


## Analysis / Comparison (detailed)

Comparison table (brief):
- Simplicity: Naïve > Sentence-Window > Parent–Child
- Precision (short factual): Sentence-Window ≥ Parent–Child > Naïve
- Contextual coherence (long-docs): Parent–Child > Naïve > Sentence-Window
- Storage cost (entries): Sentence-Window > Parent–Child > Naïve (depends on parent storage)
- Engineering effort: Naïve (low), Sentence-Window (medium), Parent–Child (high)

When to use each:
- Naïve: small corpora, quick prototypes, FAQs where answers are contiguous.
- Sentence-Window: API docs, FAQs, KBs with sentence-level facts.
- Parent–Child: manuals, legal, medical, complex policy docs, multi-turn agents requiring continuity.

Prompt & provenance best-practices (apply to all):
- Always include source metadata (doc_id, chunk_id, offsets, similarity score).
- System prompt: instruct LLM to use only provided excerpts and to say "I don’t know" if insufficient evidence.
- Limit temperature (0–0.2) for grounded answers.
- Deduplicate retrieved text and merge overlapping windows before concatenation.


## Reproducible Evaluation Plan (metrics, datasets, experiment protocol)

Metrics (implement programmatically):
- Retrieval: Recall@k (k = 1,5,10,50,100), MRR, nDCG@k.
- End-to-end generation: EM / F1 (QA), ROUGE (summaries), BERTScore.
- Faithfulness: QAGS, FEQA, FactCC; Provenance coverage ratio (fraction of claims supported by retrieved passages).
- Latency & cost: p50/p95/p99 latencies for retrieval + reranking + generation, and per-query cost.
- Human eval: binary correctness, helpfulness (Likert), hallucination presence; compute inter-annotator agreement (Cohen's kappa).

Experiment protocol (step-by-step):
1. Data split by document (avoid doc leakage): train/val/test e.g., 80/10/10.
2. Create or gather query set (real logs or synthetic from QA datasets). Reserve 1k–5k dev queries for tuning and ≥10k for final testing if possible.
3. Create gold passage links: map question → doc → span(s) (use dataset annotations or manual/crowd linking).
4. Index variants per experimental condition (chunk sizes, embeddings, index knobs).
5. For each query: compute query-embedding → retrieve K_bi candidates (100) → rerank top_n (16–32) → assemble context → generate answer.
6. Compute retrieval & end-to-end metrics, QAGS/FEQA, and log detailed traces (ids, scores, prompt used).
7. Statistical testing: use bootstrap paired test for metric differences (report p-values and effect sizes). Apply multiple-comparison correction for many pairwise tests (Benjamini-Hochberg recommended).
8. Repeat sensitivity sweeps (chunk sizes, top_k, overlap) and produce Pareto curves (accuracy vs latency vs cost).

Benchmark datasets & adaptation tips:
- BEIR (many retrieval tasks): chunk long docs and map qrels to chunks.
- MS MARCO passage (passage-level) and doc (chunk doc and link to answer spans).
- NaturalQuestions (long/short answers): use long-answer annotations for document-level retrieval mapping.
- TriviaQA, ELI5: adapt to evidence retrieval and long-form evaluation (ROUGE/BERTScore) respectively.
- Domain-specific: annotate 1k–5k queries with gold evidence linkage; for high-stakes domains use expert-labeled 500–2k examples.

Parameter grid suggestions (appendix contains explicit grids): chunk_size ∈ {100,200,400}, overlap ∈ {0,50,100}, K_bi ∈ {50,100,200}, top_n_rerank ∈ {8,16,32}.


## Index technologies & tuning (FAISS/HNSW/Milvus/Qdrant/Pinecone/Redis)

Which to choose (high level):
- HNSW (FAISS, nmslib, Qdrant/Redis): great recall and latency for up to ~1–10M vectors in RAM. Good default for dev and medium-scale production.
- FAISS IVF+PQ (+OPQ): best when memory is constrained and scale is 10s–100sM vectors; requires careful tuning and periodic retrain of quantizers.
- Milvus/Qdrant: production vector DBs that wrap FAISS/HNSW and offer persistence, filtering, snapshots.
- Pinecone: hosted managed service — easiest to operate but less low-level control and cost implications.

Key knobs and starting values:
- HNSW: M=32, ef_construction=200, ef_search=128. Increase ef_search to raise recall at cost of latency; increase M for better recall but more memory.
- FAISS (IVF+PQ): nlist ≈ 10 * sqrt(N) (start), nprobe ∈ {8,16,32}, PQ subvector count M_subvectors ∈ {8,16}, nbits=8. Use OPQ to reduce PQ error.
- Use Hybrid search where BM25 prunes candidate set before ANN retrieval when keyword signals are strong.

Latency / memory / recall recipes (approx):
- Up to 1M vectors: HNSW in-memory, expect single-digit ms retrieval on decent CPU.
- 1–10M: HNSW or sharded HNSW; add GPU only for batch or heavy writes.
- 10–100M: IVF+PQ with sharding and OPQ; expect higher p95 latency (tens to hundreds ms) unless using GPU or aggressive caching.


## Reranking strategies (bi-encoder → cross-encoder hybrid)

Design pattern: retrieve K_bi (100) using a bi-encoder, then cross-encoder rerank top_n (16–32). This balances recall and precision with runtime cost.
- Bi-encoder models: all-MiniLM-L6-v2 (384d, fast), all-mpnet-base-v2 (768d, stronger), or hosted embeddings (OpenAI text-embedding-3-*).
- Cross-encoder rerankers: cross-encoder/ms-marco-MiniLM-L-6-v2 for low-cost, larger T5/DeBERTa cross-encoders when higher precision is required.

Placement per RAG approach:
- Naïve: rerank top doc-level chunks before concatenation.
- Sentence-window: rerank top windows then merge and select non-redundant ones.
- Parent–Child: parent-first: rerank parent candidates, then retrieve/rerank children within chosen parents; child-first: rerank child candidates then map to parents.

Latency cost example (illustrative):
- Bi-encoder embed + ANN: 10–40 ms.
- Cross-encoder rerank 16 pairs on GPU: 16–80 ms; on CPU: 160–800 ms.
- Keep top_n small for CPU-only deployments.


## Embedding model selection & A/B testing

Guidance:
- Start with a mid-size model (all-mpnet-base-v2 / 768d) for development; move to larger or hosted embeddings only if metrics justify cost.
- Dimensionality trade-offs: 384d faster & cheaper; 768–1536d better recall on hard queries; 3072d (some hosted models) best recall but expensive.

A/B testing protocol (practical):
1. Define primary metric (e.g., Recall@10 or EM on downstream QA).
2. Use dev set (>=1k queries). For measured effect size δ and desired power, compute sample size (bootstrap/power analysis). As a rule-of-thumb, 1k–2k queries detect moderate effects.
3. Reindex corpus per embedding candidate.
4. Run retrieval+rerank+generate pipeline; compute metrics and latency/cost.
5. Use paired bootstrap or permutation test to compare embedding candidates; report p-values and effect sizes; correct for multiple comparisons.
6. Promote the model that meets metric & SLO constraints.


## Cost estimation (formulas and worked example)

Per-query parametric formula:
per_query_cost = cost_embed + cost_retrieval_infra + cost_rerank + cost_generation + amortized_storage_cost
where:
- cost_embed = embedding_price_per_call * #embedding_calls (usually 1 query embed)
- cost_retrieval_infra = server CPU/GPU amortized per query + vector DB cost per query
- cost_rerank = cost_per_cross_encoder_inference * num_pairs_reranked
- cost_generation = (prompt_tokens + output_tokens)/1000 * price_per_1k_tokens
- amortized_storage_cost = monthly_storage_cost / monthly_queries

Worked example (replace numbers with current vendor prices):
Assumptions:
- 1,000 queries.
- Embedding: $0.0005 per embed (approx).
- Retrieval infra (HNSW) amortized: $0.0002 per query.
- Cross-encoder cost per pair: $0.0004 (GPU amortized equivalent); num_pairs = 16.
- LLM generation cost: $0.03 per 1k tokens; average prompt+answer=500 tokens → $0.015/query.
Compute:
- cost_embed = $0.0005
- cost_retrieval_infra = $0.0002
- cost_rerank = 16 * $0.0004 = $0.0064
- cost_generation = $0.015
- per_query_cost ≈ $0.0221 → 1,000 queries = $22.10

Sensitivity: doubling top_n_rerank or using a larger LLM approximately doubles respective cost components.


## Index-scale engineering & Ops runbook (sharding, updates, backups)

Sharding & replication
- Shard by vector id abstract or consistent hashing. Run multiple index shards; route query to all shards (scatter-gather) or use routing keys when possible.
- Replicate shards for read availability and throughput.

Incremental updates & reindexing
- For embedding model changes or PQ/OPQ retrain: plan rolling reindex: build new index in parallel, backfill, switch alias.
- For frequent small updates: use DB that supports real-time upserts (Milvus, Qdrant, Pinecone); maintain write buffer and background merge.

Backups & snapshots
- Periodically snapshot index and metadata. For FAISS, persist index files + metadata mapping table. For cloud DBs use built-in snapshot features.
- Test restore annually (or on each major release) in staging.

Monitoring & alerts (suggested metrics)
- Retrieval p50/p95/p99 latency; generation latency; end-to-end latency.
- Retrieval recall@k sampled on a held-out set daily.
- Query QPS and index CPU/memory usage.
- Hallucination signal: fraction of answers failing automated faithfulness checks (QAGS/FEQA) — alert if > threshold.

Rebalancing and hot/cold tiers
- Keep hot subset of frequently accessed docs in in-memory HNSW. Archive cold vectors with compressed PQ on disk.
- Promote/demote by access count and TTL.

Incident runbook: index degradation
1. Identify symptom (latency/recall drop).
2. Check index health (shard status, memory pressure), recent reindexing/changes.
3. If recall drop after PQ retrain: rollback to previous index snapshot.
4. If latency spike: scale replicas or divert to reduced top_n and smaller cross-encoder until resolved.


## Deduplication, merging heuristics & evaluation

Heuristics (starting values; tune on dev):
- Embedding cosine duplicate threshold: ≥ 0.92 → treat as near-duplicate.
- Token Jaccard threshold: ≥ 0.6 → duplicate.
- Soft-merge: cos_sim ∈ [0.88,0.92] and Jaccard > 0.4 → consider merge.
- Adjacent gap merge: gap ≤ 50 tokens → merge windows.
- Parent coverage: if parent contains >60% of child tokens, consider parent as authoritative.

MMR for diversity: λ=0.5–0.7 (0.7 favors relevance).

Evaluation of dedup effects:
- Measure retrieval recall@k pre/post dedup (target <2% recall loss) and end-to-end EM/F1/ROUGE.
- Measure unique passages per query (reduces prompt redundancy).
- Human eval for perceived completeness and coherence.


## Hallucination detection & mitigation

Automated detection patterns:
- Provenance scoring: split answer into claims → try to match claims to retrieved passages via exact/span match or semantic similarity. Flag if <X% claims supported.
- QAGS/FEQA: generate QA pairs from output and check if answers are supported by context.
- NLI contradiction detection: test for contradictions between claims and supporting passages.

Mitigation actions:
- If provenance coverage < threshold (e.g., 60%): respond conservatively ("I don't know" or "I may be mistaken — sources below"), trigger human review for high-risk queries.
- Increase retrieval breadth (increase K) and rerun reranking; if still unsupported, escalate.
- Provide explicit inline citations per sentence and a confidence score.
- For high-assurance domains: prefer extractive answers or human-in-the-loop verification.

Human eval protocol (faithfulness):
- Sample N=200–500 answers; have labelers mark each sentence as supported/unsupported by cited sources. Compute fraction supported and Cohen's kappa.
- For domain-critical systems, use domain experts.


## Security, privacy & governance (prescriptive controls)

Encryption & network security
- Encryption at rest: enable disk-level + DB-level encryption keys (KMS) on index files and metadata.
- Encryption in transit: enforce TLS for all client and inter-node connections.

IAM & access control
- Least-privilege roles for vector DB operations (read-only for query apps, write-only for ingestion jobs).
- Signed short-lived tokens for end-user requests; rotate keys regularly.

PII & redaction
- Detect PII at ingest: regex + NER + optional LLM verification.
- Redaction options:
  - Full redaction: remove fields before indexing.
  - Masking: store masked copy and maintain original in secure vault with stricter access.
- For deletion requests: tag vectors by owner_id and provide delete-by-owner operation; if vector compression prevents exact removal, schedule reindex.

Audit trails & provenance data model
- Log: query_hash, user_id (or anonymized), timestamp, model_version, retrieved_ids + scores, reranker scores, prompt_version, output.
- Store provenance per claim: {doc_id, chunk_id, start_token, end_token, similarity_score}.

Data retention & compliance
- Retention policy: example default 90 days for raw query logs, 1–3 years for anonymized aggregates; shorter for sensitive data as required.
- GDPR/HIPAA: provide data subject access and deletion processes; design upload workflows to capture consent and tenancy.


## Risks / Trade-offs

- Cost vs Quality: cross-encoders and large embedding dims raise costs; tune to SLOs.
- Recall vs Latency: increasing ef_search/nprobe boosts recall but also latency.
- Compression (PQ) vs Accuracy: PQ reduces memory but lowers recall; retrain OPQ periodically.
- Hallucination remains a key risk; detection and conservative answer strategies are necessary.


## Conclusion

Choose a RAG approach based on corpus structure and query types. Use Naïve for simple/contained corpora, Sentence-Window for many short factual queries, and Parent–Child for long/structured documents or high-accuracy needs. Implement a reproducible evaluation harness, adopt a bi-encoder → cross-encoder hybrid retrieval pattern, tune index knobs to your scale, and instrument rigorous hallucination detection and governance controls. The provided pseudocode, hyperparameters, cost formulas, and runbooks should let an engineering team implement and iterate quickly.


## Sources (selected, 2020–2026)
- BEIR: Thakur et al., "BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models" (GitHub: UKPLab/beir)
- MS MARCO: Microsoft research pages
- NaturalQuestions: Google AI research pages
- FAISS documentation: https://github.com/facebookresearch/faiss and related FAISS + OPQ guides
- HNSW resources: nmslib / OpenSearch / Elastic blogs on HNSW tuning
- Milvus, Qdrant, Pinecone, Redis Vector docs (official project docs)
- LlamaIndex & LangChain docs for retrieval orchestration
- QAGS, FEQA, FactCC papers and implementations (factuality detection literature)
- Recent RAG surveys (2023–2025/2026) — consult arXiv for latest surveys and benchmarking papers


## Appendix A — Runnable pseudocode (concise)

Notation: embed(text) → vector; ANN.search(vec,K) → list[(id,score,meta)]; cross_rerank(query, passages) → scored list; generate(prompt) → text; tokenize, jaccard, cos_sim utilities available.

1) Naïve RAG (python-like pseudocode)

query_vec = embed(query)
docs = ANN.search(query_vec, K=10)
# optional rerank
reranked = cross_rerank(query, docs[:16])
selected = dedup_keep_top(reranked, top_m=5)
prompt = assemble_prompt(selected)
answer = generate(prompt)
return answer, selected

2) Sentence-window RAG

query_vec = embed(query)
windows = ANN.search(query_vec, K=100)
windows = merge_overlaps(windows, jaccard_thresh=0.4, gap=50)
reranked = cross_rerank(query, windows[:32])
selected = mmr_select(reranked, k=8, lambda=0.7)
prompt = assemble_prompt(selected)
answer = generate(prompt)
return answer, selected

3) Parent–Child — Parent-first

query_vec = embed(query)
parents = ANN_parent.search(query_vec, K=10)
children_candidates = []
for p in parents[:5]:
    children_candidates += ANN_child.search_within_parent(query_vec, p.id, top_k=16)
reranked = cross_rerank(query, children_candidates[:64])
selected = assemble_by_parent_limit(reranked, per_parent=3)
# optionally include parent summary
prompt = assemble_prompt(selected + parent_summaries(selected))
answer = generate(prompt)
return answer, selected

4) Parent–Child — Child-first

query_vec = embed(query)
child_hits = ANN_child.search(query_vec, K=200)
reranked = cross_rerank(query, child_hits[:64])
selected_children = dedup_merge_children(reranked, per_parent_limit=4)
selected_parents = set(c.parent_id for c in selected_children)
parent_ctxs = retrieve_parent_texts(selected_parents)
prompt = assemble_prompt(parent_ctxs + selected_children)[:token_budget]
answer = generate(prompt)
return answer, selected_children + parent_ctxs


## Appendix B — Parameter grids (suggested for experiments)
- chunk_size ∈ {100,200,400}
- overlap ∈ {0,50,100}
- sentence_window ∈ {±1,±2,±3 sentences}
- child_size ∈ {100,150,250}
- parent_size ∈ {800,1200,1800}
- K_bi ∈ {50,100,200}
- top_n_rerank ∈ {8,16,32}
- ef_search (HNSW) ∈ {64,128,256}
- nprobe (IVF) ∈ {8,16,32}
- dedup_cosine ∈ {0.88,0.9,0.92}


---

If you want, I can now:
- produce a runnable Jupyter notebook (Python) that implements the evaluation harness and the four retrieval flows (FAISS/HNSW minimal examples) using synthetic data, or
- generate concrete Terraform/Helm snippets and a starter repo scaffold for deployment.

Please tell me which artifact you prefer next (notebook, repo scaffold, or an experiment runbook with commands).