# Версії бібліотек (станом на 2026-04-14)

Нижче — посилання на сторінки релізів і примітка про останнє оновлення. Щоб уникнути хейлампазаних номерів (я не виконую додаткового веб-запиту в цій ревізії), навожу джерела та дату перевірки. Якщо хочете, можу отримати точні теги/номери версій із GitHub/PyPI/NPM і оновити звіт.

- langchain (GitHub Releases) — перевірити останній реліз тут: https://github.com/langchain-ai/langchain/releases (accessed 2026-04-14)
- langgraph (GitHub repo / releases) — https://github.com/langchain-ai/langgraph (accessed 2026-04-14)
- langsmith SDK (docs & client) — https://langsmith-sdk.readthedocs.io/ (accessed 2026-04-14)
- LangSmith Deployment (managed service) — сторінка продукту: https://www.langchain.com/langsmith/deployment (accessed 2026-04-14)

Примітка: для виробничого використання рекомендую зафіксувати точні версії пакетів у requirements.txt або package.json (pin to exact tags або semantic minor versions) і протестувати оновлення в staging.

---

# Коли достатньо LangChain, а коли краще LangGraph (LangSmith Deployment) — Порівняльний звіт

Оновлено: 2026-04-14

## Executive Summary
LangChain (OSS) — універсальна бібліотека для швидкого створення LLM-застосунків: chains, retrievers, vector stores, agents (шаблони) та широка екосистема інтеграцій. LangGraph (OSS) — графово-орієнтована бібліотека для durable, stateful та multi-agent workflows; у 2025 р. платформа керованого рантайму для довготривалих агентів була випущена й у жовтні 2025 перейменована/рефокусована на "LangSmith Deployment" (managed runtime + tooling). Для більшості простих RAG/QA/чатботів LangChain достатньо; коли потрібні стійкі, довготривалі, багатоетапні agentic системи з human-in-the-loop, стореджем стану, streaming UX та детальною трасуваністю — варто застосувати LangGraph і розглянути LangSmith Deployment для продакшен-рантайму.

Коротко:
- Використовуйте LangChain для: PoC, RAG/QA, простих агентів, швидких прототипів.
- Додайте LangGraph (і за потреби LangSmith Deployment) коли: потрібна довготривалість, multi-agent coordination, streaming/token-by-token UX, human approvals або виробнича оркестрація з трасуванням.

(Джерела: офіційна документація та блог LangChain; GitHub репозиторії — див. Sources)

---

## Findings
1) Ребрендинг та позиціонування
- LangGraph Platform (GA у 2025) переіменували/рефакторили в LangSmith Deployment (жовтень 2025). LangGraph лишається OSS для оркестрації; LangSmith Deployment — керований рантайм + інструменти для деплою long-running agents. (LangChain blog; LangSmith Deployment page) [https://blog.langchain.com/langgraph-platform-ga/ — published 2025-05-14; accessed 2026-04-14] [https://www.langchain.com/langsmith/deployment — accessed 2026-04-14].

2) Основні ролі
- LangChain (OSS): high-level composition (models, prompts, chains, retrievers, vector stores, agents шаблони), великі інтеграції з vector DB та LLM providers. (GitHub) [https://github.com/langchain-ai/langchain — accessed 2026-04-14].
- LangGraph (OSS): низькорівневі durable primitives — nodes, graphs, checkpoints, memory, human-in-the-loop hooks, streaming-first primitives для agentic workflows. (GitHub) [https://github.com/langchain-ai/langgraph — accessed 2026-04-14].
- LangSmith Deployment (managed): runtime + agent registry + autoscaling + persistence + Studio/observability для запуску LangGraph-style agents у production. (Docs) [https://www.langchain.com/langsmith/deployment — accessed 2026-04-14].

3) Ліцензія
- LangChain core та LangGraph — ліцензія MIT (OSS). LangSmith Deployment та LangSmith (observability/eval) — керовані/комерційні сервіси (деталі на pricing). [https://github.com/langchain-ai/langchain — accessed 2026-04-14] [https://github.com/langchain-ai/langgraph — accessed 2026-04-14] [https://www.langchain.com/pricing — accessed 2026-04-14].

4) Спільнота та зрілість
- LangChain — великa спільнота, активний GitHub релізний цикл, багато прикладів. LangGraph — молодший, швидко розвивається, має корпоративну підтримку через LangSmith ecosystem. (GitHub releases) [https://github.com/langchain-ai/langchain/releases — accessed 2026-04-14].

5) Observability & Tooling
- LangSmith/Studio зберігає run/tree traces, надає UI для thread views, фільтрів та експорту трас (LangSmith SDK). Використовується клієнтський SDK для list_runs/export. [https://langsmith-sdk.readthedocs.io/ — accessed 2026-04-14].

6) Комерційні пропозиції
- Public pricing tiers (Developer/Plus/Enterprise) на сайті LangChain; Enterprise пропонує hybrid/self-hosted варіанти, SSO/RBAC й SLA — деталі за запитом. (pricing) [https://www.langchain.com/pricing — accessed 2026-04-14].

---

## Analysis / Comparison
Нижче порівняно ключові аспекти та практичні наслідки вибору.

1) Функціональність: chains, agents, retrievers, vector DBs
- LangChain
  - Chains: багаті шаблони (simple, map-reduce, stuff), high-level helpers для RAG (RetrievalQA), прості agents і tools. Швидко стартувати з Python/JS SDKs.
  - Retrievers/Vector DBs: підтримка FAISS, Milvus, Pinecone, Weaviate, Redis, Chroma, pgvector тощо.
- LangGraph
  - Фокус на durable agents: explicit nodes/edges, чекпоінти, персистентна пам'ять, streaming, human approvals, multi-agent orchestration.
  - Інтегрується з LangChain компонентами (можна повторно використовувати retrievers/vector stores).

Практика: якщо ваш workflow — одноразовий RAG запит → LangChain достатньо. Якщо workflow — довготривалий, потребує збереження стану, відновлення або orchestration декількох агентів → LangGraph краще.

2) Масштабування і продуктивність
- LangChain-only: бібліотека з мінімальними накладними витратами; масштабування залежить від інфраструктури (LLM provider, vector DB, web tier). Простішe latency-sensitive сценарії виграють від простого стека.
- LangGraph + LangSmith Deployment: додає durable runtime, який може збільшити per-run latency через додаткові виклики persistence/coordination, але знижує частоту помилок та підвищує кінцеву пропускну здатність для складних workflows завдяки built-in retry, autoscale, і managed queueing.

Висновок: очікуйте невелике перетягнення латентності на одиничному виклику при посадці на LangSmith Deployment, але кращу стабільність для багатокрокових workloads.

3) Розширюваність та кастомізація
- LangChain: дуже розширювана (плагіни для models, embeddings, custom chains). Більше прикладів і готових інтеграцій.
- LangGraph: дає fine-grained control flow для агентської логіки — легше виражати складні orchestration patterns.

4) Developer ergonomics
- LangChain: низький поріг входження. Короткі приклади для RAG/QA; багата документація та community snippets.
- LangGraph: середній/вищий поріг — треба опанувати графову модель, чекпоінти та runtime deployment. LangSmith Studio допомагає debug/observe.

5) Observability і дебаг
- LangChain-only: залежить від вашої telemetry (logs/OTel/Datadog). Для multi-step agentic flows власне трасування треба имплементувати.
- LangGraph + LangSmith: вбудована модель run/tree із збереженням входів/виходів, trace search, thread views та API для експорту/run replay. (LangSmith SDK) [https://langsmith-sdk.readthedocs.io/ — accessed 2026-04-14].

6) Cost & commercial considerations
- Managed (LangSmith Deployment): швидкий time-to-prod, integrated observability; додаткові recurrent витрати (traces, managed runtime hours, storage). Enterprise support пропонує hybrid/self-host options.
- Self-hosted: нижчі recurrent vendor витрати, більше капітальних і операційних витрат на інфраструктуру та підтримку.
(Звертайтеся до sales для enterprise quotes) [https://www.langchain.com/pricing — accessed 2026-04-14].

7) Security, privacy, compliance (коротко)
- Managed: дізнавайтеся у постачальника про encryption-at-rest, KMS, VPC/private-link, SOC2/ISO сертифікації; Enterprise tier звично надає VPC/hybrid варіанти та SSO/RBAC.
- Self-hosted: контролюєте всі сервіси; імплементуйте TLS, disk encryption, app-level field encryption для PII, RBAC/SSO, retention policies та audit logging.

---

## Benchmarks & Reproducible Methodology (RAG latency + Multi-step agent throughput)
Примітка: нейтральних, публічних head-to-head бенчмарків LangChain-only vs LangChain+LangGraph/LangSmith Deployment на момент 2026-04 не знайдено. Нижче — відтворюваний план бенчмарків та ілюстративні (гіпотетичні) результати для інтерпретації.

A) Мети
- RAG latency: P50, P95 latency, tokens per call, cost-per-call.
- Multi-step agent throughput: завершення на секунду, failure/retry rate, ресурсне використання.

B) Середовища (детально для відтворення)
- Baseline (LangChain-only, self-hosted)
  - K8s cluster: 3 x n2-standard-4 (8 vCPU, 32 GB) for worker pods
  - Vector store: Milvus cluster (3 nodes) або FAISS on SSD
  - LLM provider: same external API endpoints (OpenAI/Anthropic) used for both tests
  - Telemetry: Prometheus + Grafana
- Managed (LangGraph + LangSmith Deployment)
  - LangSmith managed runtime (region matched to model provider)
  - Vector store: either self-hosted in VPC (preferred for parity) or managed
  - Observability: LangSmith Studio + exported traces to S3 for analysis

C) Workload specs
- Corpus: 10k docs (~2–5k tokens each)
- Retrieval: embedding dim 1536, search k=4, HNSW
- RAG test: run 3 trials with concurrency levels [1, 5, 20, 50]
- Agent test: N concurrent runs (10, 50, 100), each run executes:
  Step 1: retrieval
  Step 2: LLM call (plan)
  Step 3: external tool (HTTP call with 200ms latency)
  Step 4: store result in persistent memory

D) Measurement tools & metrics
- Use k6 or Python asyncio harness to generate load.
- Collect P50/P95/P99 latencies, success rate, tokens consumed, CPU/memory, and LangSmith run traces (where applicable).
- Cost metrics: LLM token costs + managed runtime costs (per-minute or per-run charge) + vector store ops.

E) Reproducibility
- Publish harness code + Dockerfiles + IaC (Terraform) to reproduce environments.

F) Illustrative (hypothetical) example — метрики для інтерпретації (НЕ виміряні в цьому звіті)
- RAG median latency (example):
  - LangChain-only (self-hosted): P50 ~ 620 ms, P95 ~ 1.2 s
  - LangChain + LangSmith Deployment: P50 ~ 760 ms, P95 ~ 1.4 s
- Multi-step agent throughput (example, 100 concurrent runs):
  - LangChain-only self-hosted: 18 completions/sec (high variance)
  - LangChain + LangSmith Deployment: 22 completions/sec (more stable, fewer retries)

Інтерпретація: managed runtime може додавати невелике пер-запит латентне оверхед, але дає кращу стабільність й менше збою у складних workflows. Проведіть тест у вашому оточенні для прийняття остаточного рішення.

---

## Migration / Integration Guidance (конкретні кроки)
Мета: швидкий PoC на LangChain → поступова міграція довготривалих потоків на LangGraph, збереження portability.

1) Початкова архітектура (PoC)
- LangChain RetrievalQA + FAISS (self-hosted) + LLM provider (OpenAI/Anthropic) + FastAPI endpoint.

2) Коли переходити на LangGraph
- Потреба у відновленні/чекпоінтах, human approvals, довготривалість (>30s або background jobs), multi-agent coordination.

3) Міграція — кроки (приклад)
- Крок A: Винесіть retriever/embeddings у окремий сервіс або endpoint (щоб легко викликати з LangGraph nodes).
- Крок B: Реалізуйте LangGraph node, що викликає існуючий retriever API (або підключається до того ж vector-store).
- Крок C: Послідовно перенесіть довготривалі flows до LangGraph; тестуйте з LangSmith Studio (або у self-hosted runtime).
- Крок D: Деплой на LangSmith Deployment або self-hosted LangGraph runtime; перевірте replay/restore на збережених трасах.

4) Minimal code snippets
- LangChain RAG (Python) — зразок
```python
# LangChain RAG (приближено)
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

emb = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = FAISS.from_texts(doc_texts, emb)
retriever = vectorstore.as_retriever(k=4)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.0)
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
print(qa.run("How do I return product X?"))
```
- LangGraph node (Python pseudocode) — reuse same vectorstore endpoint
```python
from langgraph import Node, GraphRuntime

# assume vectorstore client available

def retrieval_node(ctx, state):
    q = ctx['query']
    docs = vectorstore.similarity_search(q, k=4)
    return {'docs': docs}

node = Node(fn=retrieval_node)
graph = GraphRuntime(nodes=[node])
graph.deploy()
```
(Нотатка: точні API LangGraph можуть відрізнятись; див. GitHub репо та docs для деталей) [https://github.com/langchain-ai/langgraph — accessed 2026-04-14].

5) Rollback & testing
- Тестуйте у staging: заведіть synthetic traces, тестуйте replay. Зберігайте backward-compatible run definitions або версію графа; тримайте експортовані run-логи.

---

## Security, Privacy & Compliance (розширено)
1) Data in traces/state
- Персистентні стани та traces можуть містити PII; при використанні керованого рантайму дізнайтеся від постачальника, які поля зберігаються та де.

2) Encryption
- Managed: вимагайте customer-managed KMS або hybrid VPC опції; підтверджуйте TLS for in-transit and encryption-at-rest. (pricing/enterprise notes) [https://www.langchain.com/pricing — accessed 2026-04-14].
- Self-hosted: використовуйте KMS, disk encryption, TLS, DB-level encryption для memory stores.

3) Access control
- Enterprise tier має SSO/RBAC (перевірте пропозицію). Для self-hosted інтегруйте OIDC/SAML та розмежуйте доступ до trace export/agent management.

4) PII handling guidelines
- Prefer to filter / redact PII before storing in memory/traces.
- Tokenization and embeddings can leak PII; never store raw PII in long-term memory unless encrypted and access-controlled.

5) Auditing & retention
- Implement retention policies for traces/memory; use export/archival and periodic deletion to meet data retention regulations.

---

## Risks / Trade-offs
- Complexity vs speed: LangGraph дає потужні примітиви, але вимагає складнішої архітектури та знань.
- Vendor lock-in: managed LangSmith Deployment прискорює запуск, але додає ризик vendor coupling; мітки пом'якшення — експортуйте runs, зберігайте snapshots, та використовуйте self-hosted vector stores.
- Cost: managed traces & long-running runtime incur recurring costs; self-hosting incurs engineering+ops cost.
- Stability & churn: LangChain ecosystem швидко еволюціонує — фіксуйте версії та тестуйте апдейти у staging.

---

## Conclusion & Recommendations
1) Рекомендації за сценаріями
- PoC / одиничні RAG застосунки / невеликі чатботи: LangChain OSS + self-hosted vector DB (FAISS/pgvector) — швидко і дешево.
- Середні продукти з moderate coordination: почніть з LangChain, підготуйте retriever/embeddings як окремий сервіс; мігруйте складні flows у LangGraph коли з'явиться потреба.
- Виробничі довготривалі multi-agent системи з human-in-loop: LangGraph OSS + LangSmith Deployment (managed) рекомендовано; якщо сувора вимога до data residency — self-hosted LangGraph + інструменти для експорту трас.

2) Практичні наступні кроки
- Якщо зараз PoC: реалізуйте LangChain RAG прототип і виміряйте latency/cost.
- Якщо плануєте agentic product: заплануйте proof-of-concept LangGraph node, проведіть benchmark using the reproducible harness described вище.
- Для enterprise: зв'яжіться з LangChain sales для уточнення hybrid/SLA/SSO та запросіть data residency terms.

---

## Compact decision checklist
- Немає statefulness, швидкий PoC: LangChain.
- Потрібен durable state, resume, human approvals: LangGraph + (LangSmith Deployment if prefer managed).
- Жорстка compliance / PII: self-hosted LangGraph + on-prem vector stores; or LangSmith Enterprise hybrid with VPC/KMS.
- Fastest time-to-production with moderate compliance needs: LangGraph + LangSmith Deployment.

---

## Sources (accessed 2026-04-14)
- LangChain GitHub — https://github.com/langchain-ai/langchain
- LangChain releases/changelog — https://github.com/langchain-ai/langchain/releases
- LangGraph GitHub — https://github.com/langchain-ai/langgraph
- LangChain blog: LangGraph Platform GA (2025-05-14) — https://blog.langchain.com/langgraph-platform-ga/ (rebrand note Oct 2025)
- LangSmith Deployment page — https://www.langchain.com/langsmith/deployment
- LangChain pricing — https://www.langchain.com/pricing
- LangSmith SDK docs (run/list_runs) — https://langsmith-sdk.readthedocs.io/
- Case studies (vendor): Replit — https://blog.langchain.com/customers-replit/; Klarna — https://blog.langchain.com/customers-klarna/
- Local knowledge base: langchain.pdf (internal summary)

---

## Assumptions & Uncertainties
- Немає незалежних публічних head-to-head бенчмарків станом на 2026-04; надана методологія дозволяє виконати відтворювані тести у вашому середовищі.
- Деякі enterprise-detailed характеристики (ціни, SLA, security attestations) залежать від домовленості з продажем LangChain/LangSmith і вимагають direct inquiry.
- API/SDK синтаксис LangGraph/ LangSmith змінюється швидко; в production фіксуйте версії і перевіряйте реліз-ноти перед апгрейдом.

---

## Next steps (optional)
- Створити Dockerized benchmark harness і репозиторій з кодом для RAG + multi-step agent тестів під ваш провайдер/векторну БД.
- Підготувати архітектурний шаблон під ваш конкретний кейс (customer support RAG vs automation agent).
- Скласти чекліст для RFP/запиту до LangChain sales (hybrid, data residency, exit terms, pricing).


