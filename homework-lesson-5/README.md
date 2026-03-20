# Research Agent з RAG-системою

Інтерактивний агент, який отримує питання від користувача, самостійно шукає інформацію через набір інструментів (веб + локальна база знань) і генерує структурований Markdown-звіт.

## Швидкий старт
```bash
# 1. Клонувати репозиторій
git clone <repo-url>

# 2. Встановити залежності
pip install -r requirements.txt

# 3. Створити .env файл
cp .env.example .env
# Відкрити .env і вставити свій API-ключ

# 4. Завантажити документи у векторну БД
python ingest.py

# 5. Запустити агента
python main.py
```

## Змінні середовища

Створіть файл `.env` на основі `.env.example`:
```env
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-5-mini
```

> **Важливо:** ніколи не комітьте `.env` у git. Він вже доданий до `.gitignore`.

## Залежності
```
langchain>=1.2.0
langchain-openai>=0.3.0
langchain-community>=0.3.0
langgraph>=0.5.0
ddgs>=7.0
trafilatura>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
faiss-cpu
rank_bm25
sentence-transformers
llama-index-core
llama-index-readers-file
pypdf
```

Встановити одною командою:
```bash
pip install -r requirements.txt
```

## Структура проєкту
```
homework-lesson-5/
├── main.py              # Entry point — інтерактивний REPL
├── agent.py             # Налаштування агента (LLM, tools, memory)
├── tools.py             # web_search, read_url, write_report, knowledge_search
├── retriever.py         # Hybrid retrieval + reranking logic
├── ingest.py            # Ingestion pipeline: docs → chunks → embeddings → vector DB
├── config.py            # Settings
├── requirements.txt
├── .env.example
├── data/                # Документи для ingestion (PDF, TXT, MD)
│   └── retrieval-augmented-generation.pdf
├── output/              # Згенеровані звіти
└── README.md
```

## Інструменти агента

| Інструмент | Опис |
|---|---|
| `knowledge_search(query)` | Пошук у локальній базі знань (hybrid search + reranking) |
| `web_search(query)` | Пошук через DuckDuckGo, повертає title, url, snippet |
| `read_url(url)` | Читає повний текст сторінки (перші 5000 символів) |
| `write_report(filename, content)` | Зберігає Markdown-звіт у директорію `output/` |

## Архітектура
```
Користувач → main.py (REPL) → agent.py → LLM (OpenAI)
                                              ↓
                                    tools.py (knowledge_search / web_search / read_url / write_report)
                                              ↓
                              ┌───────────────┴───────────────┐
                         retriever.py                    DuckDuckGo / URL
                    (FAISS + BM25 + Reranker)
                              ↓
                    MemorySaver (пам'ять сесії)
                              ↓
                    output/*.md (фінальний звіт)
```

### Ingestion Pipeline
```
data/*.pdf → SimpleDirectoryReader → RecursiveCharacterTextSplitter
           → OpenAIEmbeddings → FAISS index → disk (index/)
           → chunks.json (для BM25)
```

### Hybrid Retrieval
```
query → FAISS semantic search (cosine similarity)
      + BM25 lexical search
      → EnsembleRetriever (weights: 0.6 / 0.4)
      → CrossEncoder reranker (BAAI/bge-reranker-base)
      → top_n результатів
```

- **LLM** сам вирішує, які інструменти викликати і в якій послідовності
- **knowledge_search** викликається першим для питань по локальній базі
- **MemorySaver** зберігає контекст діалогу між запитами в межах сесії
- **Ліміт кроків** (`max_iterations`) захищає від нескінченних циклів

## Приклад роботи
```
You: Що таке RAG і які є підходи до retrieval?

🔧 Tool call: knowledge_search(query="RAG retrieval approaches")
📎 Result: [3 documents found]
   - [Page 2] Retrieval-augmented generation combines...
   - [Page 5] Hybrid search approaches include...
   - [Page 3] Dense retrieval using bi-encoders...

🔧 Tool call: web_search(query="RAG retrieval techniques 2026")
📎 Result: Found 5 results...

🔧 Tool call: read_url(url="https://example.com/advanced-rag")
📎 Result: [5000 chars] Latest RAG techniques...

🔧 Tool call: write_report(filename="rag_approaches.md", content="# RAG Approaches\n...")
📎 Result: Report saved to output/rag_approaches.md

Agent: RAG — це техніка, де...
```