"""
Knowledge ingestion pipeline.

Loads documents from data/ directory, splits into chunks,
generates embeddings, and saves the index to disk.

Usage: python ingest.py
"""



from llama_index.core import SimpleDirectoryReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
import json

from config import Settings
settings = Settings()

def ingest():
   
    # 1. Load documents from config.data_dir (PDF, TXT, MD)
    documents = SimpleDirectoryReader(
    input_dir = settings.data_dir, 
    recursive=True,       #вкладені підпапки
    filename_as_id=True   #назву файлу як унікальний ідентифікатор (doc_id)
    ).load_data()

    # 2. Split into chunks using TextSplitter
    recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size, 
    chunk_overlap=settings.chunk_overlap, 
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)

    langchain_docs = []
    for doc in documents:
        chunks = recursive_splitter.split_text(doc.text)
        for chunk in chunks:
            langchain_docs.append({
                "text": chunk,
                "metadata": doc.metadata    # Варіант із збереженням метаданих
            })
    
    texts = [doc["text"] for doc in langchain_docs]
    metadatas = [doc["metadata"] for doc in langchain_docs]

    # 3. Generate embeddings
    embeddings = OpenAIEmbeddings(
    api_key=settings.api_key.get_secret_value(),
    model=settings.embedding_model
    )

    # 4. Build vector store (FAISS, Qdrant, Chroma, etc.)
    if not os.path.exists(settings.index_dir):
        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
   
        # 5. Save index to config.index_dir
        vectorstore.save_local(settings.index_dir)
    
        # 6. Save chunks for BM25 retriever (pickle or JSON)
        with open(os.path.join(settings.index_dir, "chunks.json"), "w", encoding="utf-8") as f:
            json.dump(langchain_docs, f, ensure_ascii=False, indent=4)
        


if __name__ == "__main__":
    ingest()
