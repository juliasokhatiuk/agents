# Multi-Agent Research System

Багатоагентна система для автоматичного дослідження тем. Supervisor оркеструє цикл Plan → Research → Critique, генерує структурований Markdown-звіт і запитує підтвердження перед збереженням (HITL).

## Архітектура

```
Користувач → Supervisor
                 ↓
              Planner → ResearchPlan
                 ↓
             Researcher → (knowledge_search / web_search / read_url)
                 ↓
               Critic → CritiqueResult (APPROVE / REVISE)
                 ↓
            save_report ← [HITL: approve / edit / reject]
                 ↓
           output/*.md
```

**Агенти:**
| Агент | Роль |
|---|---|
| `Supervisor` | Оркеструє цикл, керує HITL |
| `Planner` | Декомпозує запит у `ResearchPlan` |
| `Researcher` | Збирає інформацію з веб + локальної БД |
| `Critic` | Оцінює звіт: freshness, completeness, structure |

**Інструменти Researcher:**
| Інструмент | Опис |
|---|---|
| `knowledge_search(query)` | Hybrid search (FAISS + BM25) + CrossEncoder reranker |
| `web_search(query)` | DuckDuckGo, повертає title / url / snippet |
| `read_url(url)` | Витягує повний текст сторінки |

## Швидкий старт

```bash
# 1. Встановити залежності
uv sync

# 2. Створити .env
cp .env.example .env
# Вставити API_KEY і (опціонально) HF_TOKEN

# 3. Завантажити документи у векторну БД
uv run python ingest.py

# 4. Запустити
uv run python main.py
```

## Змінні середовища

```env
API_KEY=sk-...
MODEL_NAME=gpt-4o-mini     # опціонально, є дефолт
HF_TOKEN=hf_...            # опціонально, для HuggingFace моделей
```

## Структура проєкту

```
homework-lesson-8/
├── main.py              # Entry point — інтерактивний REPL з HITL
├── supervisor.py        # Supervisor agent (LangGraph + HumanInTheLoopMiddleware)
├── tools.py             # plan / research / critique / save_report / web_search / read_url / knowledge_search
├── agents/
│   ├── planner.py       # Planner agent → ResearchPlan
│   ├── research.py      # Research agent
│   └── critic.py        # Critic agent → CritiqueResult
├── retriever.py         # Hybrid retrieval + reranking
├── ingest.py            # PDF/TXT → chunks → FAISS + BM25 index
├── schemas.py           # ResearchPlan, CritiqueResult Pydantic схеми
├── config.py            # Settings + system prompts
├── test_agents.py       # pytest тести для кожного агента + supervisor
├── pyproject.toml
├── .env.example
├── data/                # Документи для ingestion
├── index/               # FAISS індекс + BM25 chunks (генерується ingest.py)
└── output/              # Збережені Markdown-звіти
```

## HITL (Human-in-the-Loop)

Перед збереженням звіту система зупиняється і запитує дію:

```
============================================================
  ACTION REQUIRES APPROVAL
============================================================
  Tool:  save_report
  File:  report.md
  Size:  12500 chars
============================================================

Action (approve / edit / reject):
```

| Дія | Поведінка |
|---|---|
| `approve` | Зберігає звіт |
| `edit` | Supervisor переписує звіт за фідбеком, зберігаючи весь попередній контент |
| `reject` | Скасовує збереження |

## Запуск тестів

```bash
uv run --with pytest pytest test_agents.py -v -s
```

Тести перевіряють: `test_planner_agent`, `test_research_agent`, `test_critic_agent`, `test_supervisor` (повний цикл з auto-approve).
