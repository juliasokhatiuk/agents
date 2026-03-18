# Research Agent — власний ReAct Loop

Інтерактивний агент, який отримує питання від користувача, самостійно шукає інформацію через набір інструментів і генерує структурований Markdown-звіт. Реалізований **без фреймворкових абстракцій** — власний ReAct loop поверх OpenAI API.

## Швидкий старт

```bash
# 1. Клонувати репозиторій
git clone <repo-url>

# 2. Встановити залежності
pip install -r requirements.txt

# 3. Створити .env файл
cp .env.example .env
# Відкрити .env і вставити свій API-ключ

# 4. Запустити
python main.py
```

## Змінні середовища

Створіть файл `.env` на основі `.env.example`:

```env
API_KEY = "sk-your-api-key-here"
MODEL_NAME=gpt-5-mini
```

> **Важливо:** ніколи не комітьте `.env` у git. Він вже доданий до `.gitignore`.

## Залежності

```
openai>=1.0.0
ddgs>=7.0
trafilatura>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
```

Встановити одною командою:

```bash
pip install -r requirements.txt
```

## Структура проєкту

```
research-agent/
├── main.py              # Entry point — інтерактивний REPL
├── agent.py             # Власний ReAct loop (без create_react_agent)
├── tools.py             # Функції + JSON Schema для кожного tool
├── config.py            # System prompt, налаштування
├── requirements.txt
├── .env.example
├── output/
│   └── naive_rag_vs_sentence_window.md
└── README.md
```

## Інструменти агента

| Інструмент | Опис |
|---|---|
| `web_search(query)` | Пошук через DuckDuckGo, повертає title, url, snippet |
| `read_url(url)` | Читає повний текст сторінки (перші 5000 символів) |
| `write_report(filename, content)` | Зберігає Markdown-звіт у директорію `output/` |

Кожен інструмент описаний у форматі **JSON Schema** для OpenAI tool calling API — без `@tool` декоратора LangChain.

## Архітектура

```
Користувач → main.py (REPL)
                  ↓
             agent.py — власний ReAct loop
                  ↓
          OpenAI API (tool calling)
                  ↓
          tools.py (web_search / read_url / write_report)
                  ↓
          working_memory (список messages — ручна пам'ять сесії)
                  ↓
          output/*.md (фінальний звіт)
```

**Що робить ReAct loop:**
1. Відправляє `messages` + `tools` в OpenAI API
2. Якщо відповідь містить `tool_calls` — виконує їх і додає результати в `messages`
3. Повторює до фінальної відповіді або досягнення `max_iterations`

**Порівняно з homework-lesson-3:**

| homework-lesson-3 | homework-lesson-4 |
|---|---|
| `create_react_agent` | Власний цикл `while` |
| `MemorySaver` | Ручний список `working_memory` |
| `@tool` декоратор | JSON Schema для кожного tool |
| Базовий system prompt | Промпт з роллю, прикладами, обмеженнями |

## Приклад роботи

```
You: Порівняй naive RAG та sentence-window retrieval

🔧 Tool call: web_search(query="naive RAG retrieval "naive RAG"")
📎 Result: Found 5 results...

🔧 Tool call: web_search(query="sentence-window retrieval sentence window retrieval RAG 'sentence-window' 'sentence window' retrieval")
📎 Result: Found 5 results...

🔧 Tool call: read_url(url="https://docs.haystack.deepset.ai/docs/sentencewindowretrieval")
📎 Result: [147 chars] {"status": "error", "message": "The page at https://docs.haystack.deepset.ai/doc...

🔧 Tool call: read_url(url="https://learn.deeplearning.ai/courses/building-evaluating-advanced-rag/lesson/4/sentence-window-retrieval")
📎 Result: [4361 chars] 💻 Accessing Utils File and Helper Functions In each notebook on the top menu: 1:...

🔧 Tool call: write_report(filename="naive_rag_vs_sentence_window.md", content="# Порівняння: Naive RAG vs Sentence-Window Retriev...")
📎 Result: Report saved to output/naive_rag_vs_sentence_window.md

Agent: Готово — звіт збережено як naive_rag_vs_sentence_window.md.

