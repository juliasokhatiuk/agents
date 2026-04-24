# Multi-Agent Research System — Testing (homework-lesson-10)

Розширення `homework-lesson-8`: та сама мультиагентна система + автоматизоване тестове покриття на базі DeepEval.

## Архітектура системи

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

| Агент | Роль |
|---|---|
| `Supervisor` | Оркеструє цикл, керує HITL |
| `Planner` | Декомпозує запит у `ResearchPlan` |
| `Researcher` | Збирає інформацію з веб + локальної БД |
| `Critic` | Оцінює звіт: freshness, completeness, structure |

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
homework-lesson-10/
├── tests/
│   ├── golden_dataset.json     # 12 golden examples (happy path + edge cases + failure cases)
│   ├── create_golden_data.py   # Генерація golden dataset через Ragas TestsetGenerator
│   ├── test_planner.py         # Planner agent — Plan Quality (GEval)
│   ├── test_researcher.py      # Research agent — Groundedness (GEval)
│   ├── test_critic.py          # Critic agent — Critique Quality (GEval)
│   ├── test_tools.py           # Tool Correctness — Planner + Researcher + Supervisor
│   └── test_e2e.py             # End-to-end evaluation на golden dataset
├── agents/
│   ├── planner.py
│   ├── research.py
│   └── critic.py
├── main.py
├── supervisor.py
├── tools.py
├── retriever.py
├── ingest.py
├── schemas.py
├── config.py
├── pyproject.toml
├── .env.example
├── data/                       # Документи для ingestion
├── index/                      # FAISS індекс + BM25 chunks
└── output/                     # Збережені Markdown-звіти + e2e_results.csv
```

## Тести

### Запуск окремих тестів

```bash
uv run python -m tests.test_planner
uv run python -m tests.test_critic
uv run python -m tests.test_tools
uv run python -m tests.test_e2e
```

### Метрики

| Тест | Метрика | Threshold |
|---|---|---|
| `test_planner.py` | Plan Quality (GEval) | 0.7 |
| `test_critic.py` | Critique Quality (GEval) | 0.7 |
| `test_researcher.py` | Groundedness (GEval) | 0.7 |
| `test_tools.py` | Tool Correctness | 0.5 |
| `test_e2e.py` | Answer Relevancy, Correctness, Citation Presence | 0.7 / 0.6 / 0.5 |

### Очікуваний вивід test_e2e

```
test_golden_dataset [15/20 passed]
     Correctness: avg 0.74, min 0.42, max 0.95
     Answer Relevancy: avg 0.81, min 0.55, max 0.98
     Citation Presence: avg 0.70, min 0.30, max 1.00
```

### Golden Dataset

12 прикладів у `tests/golden_dataset.json`:

| Категорія | Кількість | Опис |
|---|---|---|
| `happy_path` | 4 | Типові дослідницькі запити |
| `edge_case` | 4 | Неоднозначні або широкі теми |
| `failure_case` | 4 | Запити поза доменом, безглузді запити |

Згенеровано через Ragas `TestsetGenerator` + manual review.

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
| `edit` | Supervisor переписує звіт за фідбеком |
| `reject` | Скасовує збереження |
