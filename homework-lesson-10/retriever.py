"""
Hybrid retrieval module.

Combines semantic search (vector DB) + BM25 (lexical) + cross-encoder reranking.
"""

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
import os
import json

from config import Settings
settings = Settings()

def get_retriever():
    
    # Load vector store from disk (config.index_dir)

    embeddings = OpenAIEmbeddings(
        api_key=settings.api_key.get_secret_value(),
        model=settings.embedding_model
        )

    vectorstore = FAISS.load_local(settings.index_dir, embeddings, allow_dangerous_deserialization=True)

    # 2. Create semantic retriever from vector store
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": settings.retrieval_top_k})

    # 3. Load chunks and create BM25 retriever
    with open(os.path.join(settings.index_dir, "chunks.json"), "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)

    bm25_retriever = BM25Retriever.from_texts(
        texts=[doc["text"] for doc in raw_chunks],
        metadatas=[doc["metadata"] for doc in raw_chunks])
    bm25_retriever.k = settings.retrieval_top_k

    # 4. Combine into ensemble retriever (semantic + BM25)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.6, 0.4] )
    
    # 5. Add cross-encoder reranker on top
    reranker_model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")

    compressor  = CrossEncoderReranker(
        model=reranker_model,
        top_n=settings.rerank_top_n
    )

    # 6. Return the final retriever
    reranking_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=ensemble_retriever
    )

    return reranking_retriever
