# Multi-Agent Research System — MCP + ACP

Розширення homework-8: та сама мультиагентна система Plan → Research → Critique, але вся комунікація між агентами та інструментами йде через протоколи **MCP** (Model Context Protocol) та **ACP** (Agent Communication Protocol).

## Архітектура

```
User (REPL)
  │
  ▼
Supervisor Agent (локальний, create_agent)
  │
  ├── plan(request)          ──► ACP :8903 ──► Planner Agent  ──► MCP :8901 (SearchMCP)
  │                                                                  web_search
  │                                                                  knowledge_search
  │
  ├── research(plan)         ──► ACP :8903 ──► Researcher Agent ──► MCP :8901 (SearchMCP)
  │                                                                  web_search
  │                                                                  read_url
  │                                                                  knowledge_search
  │
  ├── critique(findings)     ──► ACP :8903 ──► Critic Agent    ──► MCP :8901 (SearchMCP)
  │       │                                                          web_search
  │       ├── REVISE → повернутись до Researcher (max 2 рази)        knowledge_search
  │       └── APPROVE → перейти до save_report
  │
  └── save_report(...)       ──► MCP :8902 (ReportMCP)
                                  save_report [HITL gated]
```

## Що змінилось порівняно з homework-8

| Було (homework-8) | Стало (homework-9) |
|---|---|
| Tools як Python-функції в одному процесі | Tools виставлені як MCP сервери (FastMCP) |
| Агенти як `@tool`-обгортки для Supervisor | Агенти доступні через ACP сервер (acp-sdk) |
| Все в одному процесі | Кожен MCP/ACP сервер — окремий HTTP endpoint |
| Прямий виклик функцій | Discovery → Delegate → Collect через протоколи |

## MCP Сервери

| Сервер | Порт | Tools | Resources |
|---|:---:|---|---|
| **SearchMCP** | 8901 | `web_search`, `read_url`, `knowledge_search` | `resource://knowledge-base-stats` |
| **ReportMCP** | 8902 | `save_report` | `resource://output-dir` |

## ACP Сервер

Один ACP сервер (порт 8903) з трьома агентами:

| Агент | Опис |
|---|---|
| `planner` | Декомпозує запит у `ResearchPlan` |
| `researcher` | Збирає інформацію з веб + локальної БД |
| `critic` | Оцінює звіт: freshness, completeness, structure → `CritiqueResult` |

## Структура проєкту

```
homework-lesson-9/
├── main.py              # REPL з HITL interrupt/resume loop
├── supervisor.py        # Supervisor agent + ACP delegation tools
├── acp_server.py        # ACP server: planner, researcher, critic
├── mcp_servers/
│   ├── search_mcp.py    # SearchMCP: web_search, read_url, knowledge_search
│   └── report_mcp.py    # ReportMCP: save_report
├── agents/
│   ├── planner.py       # Planner Agent
│   ├── research.py      # Research Agent
│   └── critic.py        # Critic Agent
├── schemas.py           # ResearchPlan, CritiqueResult
├── mcp_utils.py         # mcp_tools_to_langchain helper
├── config.py            # Settings + system prompts
├── retriever.py         # Hybrid retrieval (FAISS + BM25 + CrossEncoder)
├── ingest.py            # PDF/TXT → chunks → FAISS + BM25 index
├── data/                # Документи для RAG
├── index/               # FAISS індекс + chunks.json (генерується ingest.py)
└── output/              # Збережені Markdown-звіти
```

## Порядок запуску

```bash
# 1. Встановити залежності
uv sync

# 2. Створити .env
cp .env.example .env
# Вставити API_KEY і (опціонально) HF_TOKEN

# 3. Завантажити документи у векторну БД (якщо не зроблено)
python ingest.py

# 4. Запустити MCP сервери (окремі термінали)
python -m mcp_servers.search_mcp   # порт 8901
python -m mcp_servers.report_mcp   # порт 8902

# 5. Запустити ACP сервер (окремий термінал)
python acp_server.py               # порт 8903

# 6. Запустити Supervisor REPL
python main.py
```

## Змінні середовища

```env
API_KEY=sk-...
MODEL_NAME=gpt-4o-mini
HF_TOKEN=hf_...         # опціонально, для HuggingFace reranker
SEARCH_MCP_URL=http://127.0.0.1:8901/mcp
REPORT_MCP_URL=http://127.0.0.1:8902/mcp
ACP_URL=http://127.0.0.1:8903
```

## Приклад роботи

```
You: Compare RAG approaches: naive, sentence-window, and parent-child

[Supervisor → ACP → Planner]
  Planner connects to SearchMCP for preliminary search
  Returns: ResearchPlan(goal="Compare RAG methods...", search_queries=[5 queries], ...)

[Supervisor → ACP → Researcher]  (round 1)
  Researcher connects to SearchMCP (web_search + knowledge_search)
  Returns findings: [19614 chars, 246 lines]

[Supervisor → ACP → Critic]  (round 1)
  Critic connects to SearchMCP for fact-checking
  Returns: CritiqueResult(verdict="REVISE" [⚠️  REVISE], gaps=[12 items], ...)

[Supervisor → ACP → Researcher]  (round 2)
  Returns findings: [41053 chars, 465 lines]

[Supervisor → ACP → Critic]  (round 2)
  Returns: CritiqueResult(verdict="APPROVE" [✅ APPROVE])

[Supervisor → MCP → ReportMCP]
  ⏸️  ACTION REQUIRES APPROVAL
  File: rag_comparison.md  |  Size: 17877 chars
  👉 approve / edit / reject: approve
  ✅ Report saved to output/rag_comparison.md
```

## HITL (Human-in-the-Loop)

| Дія | Поведінка |
|---|---|
| `approve` | Зберігає звіт через ReportMCP |
| `edit` | Supervisor переписує звіт за фідбеком, зберігаючи контент |
| `reject` | Скасовує збереження |
