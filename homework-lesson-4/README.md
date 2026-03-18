# Research Agent

Інтерактивний агент, який отримує питання від користувача, самостійно шукає інформацію через набір інструментів і генерує структурований Markdown-звіт.

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
OPENAI_API_KEY=sk-...        # або інший провайдер
MODEL_NAME=gpt-5-mini

```

> **Важливо:** ніколи не комітьте `.env` у git. Він вже додан до `.gitignore`.

## Залежності

```
langchain>=1.2.0
langchain-openai>=0.3.0
langgraph>=0.5.0
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
├── agent.py             # Налаштування агента (LLM, tools, memory)
├── tools.py             # Визначення та реалізація інструментів
├── config.py            # System prompt, налаштування, константи
├── requirements.txt
├── .env.example         # Шаблон змінних середовища
├── output/
│   └── comparison_naive_sentencewindow_parentchild.md        # Приклад згенерованого звіту
└── README.md
```

## Інструменти агента

| Інструмент | Опис |
|---|---|
| `web_search(query)` | Пошук через DuckDuckGo, повертає title, url, snippet |
| `read_url(url)` | Читає повний текст сторінки (перші 5000 символів) |
| `write_report(filename, content)` | Зберігає Markdown-звіт у директорію `output/` |

## Архітектура

Агент побудований на **LangGraph** + **LangChain** за патерном ReAct:

```
Користувач → main.py (REPL) → agent.py → LLM (OpenAI)
                                              ↓
                                    tools.py (web_search / read_url / write_report)
                                              ↓
                                    MemorySaver (пам'ять сесії)
                                              ↓
                                    output/*.md (фінальний звіт)
```

- **LLM** сам вирішує, які інструменти викликати і в якій послідовності
- **MemorySaver** зберігає контекст діалогу між запитами в межах сесії
- **Ліміт кроків** (`max_iterations`) захищає від нескінченних циклів
- **Обрізка результатів** — `read_url` повертає не більше 5000 символів, щоб не переповнити контекстне вікно

## Приклад роботи

```
You: Порівняй naive RAG, sentence-window та parent-child retrieval
→ web_search({'query': "naive RAG sentence-window parent-child retrieval 'parent-child retrieval' 'sentence windo)  
→ read_url({'url': 'https://medium.com/@harsh_77214/)      
→ web_search({'query': "parent-child retrieval RAG 'parent-child' retrieval 'auto-merge' 'parent section' 'merged)    
→ read_url({'url': 'https://developers.llamaindex.ai/python/examples/retrievers/})
→ write_report({'filename': 'comparison_naive_sentencewindow_parentchild.md')  

Agent: Я підготував порівняльний звіт (у Markdown) по naive RAG, sentence‑window та parent‑child (auto‑merge) retrieval, включно з визначеннями, технічною логікою, перевагами/недоліками, практичними порадами та емпіричними спостереженнями. Файл збережено як comparison_naive_sentencewindow_parentchild.md.
```


## Зміна LLM-провайдера

У `agent.py` достатньо замінити один рядок:

```python
# OpenAI (за замовчуванням)
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model=settings.model_name)

# Anthropic
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-5")

# Google
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
```
