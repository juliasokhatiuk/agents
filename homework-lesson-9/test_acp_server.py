from acp_sdk.client import Client as ACPClient
from acp_sdk.models import Message, MessagePart
from config import settings
import asyncio

ACP_BASE = settings.acp_url

async def demo_acp():
    async with ACPClient(base_url=ACP_BASE, headers={"Content-Type": "application/json"}) as client:
        # Discovery
        agents = [a async for a in client.agents()]
        print("ACP Discovery:")
        for a in agents:
            print(f"   {a.name}: {a.description}")
        print()

        # Call planner
        print('-' * 50)
        print("Calling 'planner'...")
        run = await client.run_sync(
            agent="planner",
            input=[Message(role="user", parts=[MessagePart(content="What is BM25 algorithm and how is it used in search engines?")])],
        )
        output = run.output[-1].parts[0].content
        print(f"**Result:**\n{output}")
        print()

        # Call researcher
        print('-' * 50)
        print("Calling 'researcher'...")
        run = await client.run_sync(
            agent="researcher",
            input=[Message(role="user", parts=[MessagePart(content="What is BM25 algorithm and how is it used in search engines?")])],
        )
        output = run.output[-1].parts[0].content
        print(f"**Result:**\n{output}")
        print()

        # Call critic
        print('-' * 50)
        print("Calling 'critic'...")
        run = await client.run_sync(
            agent="critic",
            input=[Message(role="user", parts=[MessagePart(content="""RAG Overview

            Retrieval-Augmented Generation (RAG) combines a retrieval system with a generative model.
            Documents are indexed in a vector store; at query time, relevant chunks are fetched and
            passed as context to the LLM, which generates a grounded answer.

            Sources:
            - https://arxiv.org/abs/2005.11401 (Lewis et al., 2020)""")])],
                )
        output = run.output[-1].parts[0].content
        print(f"**Result:**\n{output}")
        print()

asyncio.run(demo_acp())

# python test_acp_server.py

# --------------------------------------------------
# ACP Discovery:
#    planner: Agent that creates a research plan based on a user request.
#    researcher: Agent that conducts research based on the research plan and gathers findings.
#    critic: Agent that critiques the research results and provides feedback for improvement.

# --------------------------------------------------
# Calling 'planner'...
# **Result:**
# {"goal": "Explain BM25 and its role in search engines", "search_queries": ["BM25 algorithm explanation formula and probabilistic retrieval intuition", "BM25 parameters k1 b term frequency and document length normalization typical values", "BM25 implementation in Lucene and Elasticsearch with code examples and defaults", "BM25 vs TF-IDF differences advantages disadvantages 

# --------------------------------------------------
# Calling 'researcher'...
# **Result:**
# Overview
# - BM25 (Okapi BM25) is a classical, widely used lexical ranking function in information retrieval that scores and ranks documents by how well they match a keyword query. It is a refined TF–IDF style formula that includes term frequency saturation and document-length normalization. Search engines and retrieval systems commonly use BM25 as a fast initial scorer or baseline. 

# Key information
# - Intuition
#   - BM25 gives each query term a contribution to a document’s score that grows with term frequency but with diminishing returns, is down-weighted for very common terms (IDF), and is adjusted for document length (so long documents are not unfairly favored).
# - Core formula (one common instantiation)
#   - For a query Q and document D, BM25 score is the sum over query terms q of:
#     score(D,Q) = sum_q IDF(q) * ( (f(q,D) * (k1 + 1)) / (f(q,D) + k1 * (1 - b + b * |D|/avgdl)) )
#     where:
#     - f(q,D) = term frequency of q in document D
#     - |D| = document length (words)
#     - avgdl = average document length in the collection
#     - k1 and b = tunable parameters (typical defaults: k1 ≈ 1.2–1.5, b ≈ 0.75)
#     - IDF(q) is often computed as: log((N - n_q + 0.5) / (n_q + 0.5)), where N = total documents, n_q = number of documents containing q
# - Parameters meaning
#   - k1 controls TF saturation: higher k1 → more weight to term frequency.
#   - b controls length normalization: b = 1 → full normalization by document length; b = 0 → no length normalization.
# - Why it’s useful in search engines
#   - Fast to compute with an inverted index (only per-term statistics needed).
#   - Robust, interpretable, and strong baseline for many collections and queries.
#   - Often used as the “first-stage” or candidate retriever that returns top-k documents for more expensive downstream processing (e.g., neural re-rankers or passage-level scoring).
# - Common variants and extensions
#   - BM25F: extends BM25 to multiple fields (title, body, anchor text) with field-specific weights.
#   - Passage-level BM25: apply BM25 to passages instead of whole documents to improve precision for long documents.
#   - Combined pipelines: BM25 + dense (embedding) retrieval, and BM25 results can be fed to neural re-rankers (BERT-style) or 
# combined via learning-to-rank.
# - Limitations
#   - Bag-of-words: ignores term order, proximity, and phrase matching.
#   - No semantics: cannot match synonyms or latent semantic similarity (addressed by dense retrievers).
#   - Sensitive to parameter tuning and collection statistics.
# - Implementation & tooling
#   - BM25 is implemented as the default scoring model in many search libraries (Lucene/Elasticsearch, Whoosh, Terrier, Solr). 
# It uses inverted indexes and precomputed document frequency and length statistics for efficiency.

# Comparison / details (short)
# - BM25 vs TF–IDF
#   - Both use IDF-like weighting; BM25 adds a principled TF saturation term and document-length normalization which usually yields better ranking than raw TF–IDF.
# - BM25 vs dense (embedding) retrieval
#   - BM25 excels on exact lexical matches and is fast; dense retrieval captures semantic matches (synonyms, paraphrases). Modern systems often combine both: BM25 for recall and speed, dense for semantic coverage, then neural re-ranker for final quality.

# Key takeaways
# - BM25 is a simple, interpretable, and effective bag-of-words ranking function used widely in search engines as an initial or baseline scorer.
# - Its strengths are speed and reliability for lexical matching; weaknesses are lack of semantic understanding and term-dependency modeling.
# - In modern retrieval pipelines it’s common to combine BM25 with dense retrieval and neural re-ranking to get the best of both lexical precision and semantic relevance.

# Sources
# - Okapi BM25 — Wikipedia (explains formula, parameters, variants) [web]
#   - https://en.wikipedia.org/wiki/Okapi_BM25
# - Retrieval- and LLM-related notes mentioning retrieval pipelines and reranking (local knowledge base) [local]
#   - retrieval-augmented-generation.pdf (mentions pre-retrieval techniques, reranking, pipelines) [local]
#   - large-language-model.pdf (context on embedding/retrieval usage in modern systems) [local]

# --------------------------------------------------
# Calling 'critic'...
# **Result:**
# {"verdict": "REVISE", "is_fresh": false, "is_complete": false, "is_well_structured": false, "strengths": ["Concise and correct high-level definition of RAG (retrieval + generation).", "Accurately describes the core pipeline: documents indexed in a vector store, retrieval of relevant chunks, and LLM generation grounded on those chunks.", "Cites the original RAG paper (Lewis et al., 2020) as the primary source."], "gaps": ["No coverage of important RAG variants and decoding strategies (e.g., RAG-Sequence vs RAG-Token, Fusion-in-Decoder).", "Missing key follow-up retrieval models and methods that are commonly paired with RAG (e.g., Dense Passage Retrieval (DPR) and other dense/sparse/hybrid retrievers).", "No mention of benchmarking and evaluation resources for retrieval-augmented systems (e.g., BEIR) or appropriate evaluation metrics for retrieval+generation. ", "Tooling and infrastructure absent: vector search libraries and vector DBs (FAISS, Milvus, Pinecone, etc.), and how they affect latency/scale. ", "Practical implementation details missing: chunking strategies, embedding model choices, k (number of retrieved passages), context-window/concatenation approaches, caching, index update strategies for dynamic corpora. ", "No discussion of common failure modes and risks (hallucination despite retrieval, retrieval noise, citation/attribution issues, privacy/data leakage), nor mitigation strategies. ", "No discussion of applications, limitations, or trade-offs (accuracy vs latency, cost, model size).", "References are not up-to-date \u2014 overview relies on the 2020 source but omits major literature from 2020\u20132025 and standard engineering references and OSS implementations (Hugging Face, LangChain, Haystack).", "Structure is a single short paragraph without sections, examples, diagrams, or a clear audience/goal statement; not report-ready."], "revision_requests": ["Add a short structured outline (Abstract, Background, Variants, Retrieval methods, Indexing & tooling, Evaluation, Implementation checklist, Risks & mitigations, Applications, References).", "Expand 'Variants' to explain RAG-Sequence vs RAG-Token and mention alternative fusion/decoding approaches (e.g., Fusion-in-Decoder) with citations.", "Add a 'Retrievers' section describing dense, sparse and hybrid retrievers; cite Dense Passage Retrieval (DPR) and discuss when to use each type.", "Include an 'Indexing & Tooling' section listing and briefly comparing FAISS, Milvus, Pinecone (and mention embedding providers), and note how index choice affects latency and scale.", "Add an 'Evaluation & Benchmarks' section covering BEIR and recommended metrics (context precision/recall, end-task metrics, faithfulness/factuality measures), with guidance on evaluation recipes.", "Provide implementation-level guidance: chunk size heuristics, embedding model selection, retrieval k, prompt/context concatenation strategies, caching, index rebuilding/updating strategies for streaming or frequently changing data. ", "Add a 'Failure Modes & Mitigations' section addressing hallucinations, hallucination-detection, provenance/citation generation, and privacy considerations (PII handling, redaction).", "Include example references and links to canonical implementations and code (RAG paper code, Hugging Face RAG implementations, LangChain/Haystack examples) and add recommended further reading from 2020\u20132025. ", "Update the bibliography to include key follow-up work (e.g., DPR 2020; Fusion-in-Decoder 2021; BEIR 2021) and any important 2022\u20132025 advances relevant to RAG, and indicate the date of the literature sweep to make freshness explicit."]}