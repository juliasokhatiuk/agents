# Що таке RAG і які є підходи до retrieval?

## Огляд
Retrieval-Augmented Generation (RAG) — підхід, що поєднує генеративну модель (LLM) з механізмом пошуку зовнішніх документів. Замість того, щоб повністю покладатися на знання, закладені в параметрах моделі, RAG витягує релевантні фрагменти з корпусу (векторний/лексичний індекс) і додає їх як контекст до запиту перед генерацією відповіді. Це дає змогу отримувати свіжу, доменно-специфічну та більш достовірну інформацію без перетраєння моделі.

Джерела: локальний огляд RAG (retrieval-augmented-generation.pdf) [local], стаття Lewis et al. 2020 — "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" [web].

---

## Ключова інформація
- Основні компоненти RAG pipeline:
  1. Інгестія та chunking документів (розбиття на параграфи/фрагменти).
  2. Індексація: створення embeddings (dense) або інвертованих індексів (sparse).
  3. Retrieval: пошук top-k релевантних фрагментів за запитом.
  4. (Опціонально) Фільтрація / reranking / мультимодальна узгодженість.
  5. Генерація: LLM отримує запит + retrieved контекст і формує відповідь.

- Варіанти RAG (за Lewis et al., 2020):
  - RAG-sequence: модель умовлюється на одному наборі passage'ів для всієї згенерованої послідовності.
  - RAG-token (перекладено як можливість використовувати різні passage для кожного токена): дозволяє вибирати різні джерела під час генерації токенів.

---

## Підходи до retrieval
1. Лексичні (sparse) retrievers
   - Приклади: BM25 (класичний), SPLADE.
   - Переваги: швидко, інтерпретовані, добре для точного матчингу (коди, імена, специфічні терміни).
   - Обмеження: погано ловить синонімію та семантичні відношення.

2. Семантичні (dense) retrievers
   - Приклади: DPR, Sentence-BERT, bi-encoder архітектури; ColBERT (late interaction).
   - Механіка: документи та запити кодуються в вектори; пошук по ANN (FAISS, ScaNN, Milvus).
   - Переваги: знаходять семантично релевантні фрагменти.
   - Обмеження: витрати на індексацію, залежність від якості embeddings, дрейф домену.

3. Гібридні підходи
   - Комбінація sparse + dense (паралельний пошук + fusion або BM25 як фільтр перед vector search).
   - Часто дають кращий recall у реальних наборах даних.

4. Багатоступеневий retrieval (multistage)
   - Перший рівень: швидкий пошук для великого пулу (наприклад top-100).
   - Другий рівень: точний reranking (cross-encoder або neural re-ranker) для вибору фінальних top-k.
   - Зменшує latency/витрати та підвищує точність.

5. Реранкінг (re-ranking)
   - Cross-encoder (BERT-подібні моделі) для високоточних оцінок пара (запит, документ).
   - Instruction-based rerankers (LLM-оцінювання по критеріям: фактичність, стиль, довіра).

6. Тренування ретривера та вдосконалення
   - Pretraining tasks: Inverse Cloze Task (ICT) для ініціалізації.
   - Supervised contrastive learning (DPR): позитивні/негативні приклади.
   - Weak supervision / LLM-weak-labeling, distillation і alignment з генератором (напр., мінімізація KL).

7. Сучасні модифікації та інновації
   - HyDE (Hypothetical Document Embeddings): генерація "гіпотетичного" документа LLM, вбудовування його для кращого retrieval.
   - RETRO-подібні архітектури: інтеграція retrieved chunks всередину мережі (chunked cross-attention) замість простого додавання в prompt.
   - Agentic RAG, Multi-hop RAG: рекурсивні або багатокрокові стратегії для складних запитів.

---

## Практичні поради / інженерні моменти
- Вибір методів залежить від задачі:
  - BM25 або гібрид: коли потрібна точна відповідність або є технічні коди.
  - Dense retriever + ANN: для семантичних QA, FAQ, підтримки.
  - Multistage + cross-encoder: для додаткової точності у критичних застосунках.

- Параметри, що впливають:
  - Розмір chunk (sentence vs paragraph vs doc).
  - Значення k для retrieval (баланс recall vs latency).
  - Метадані та фільтри (час, авторство, source reliability).

- Метрики: Recall@k (ключова для retrieval), MRR, Precision@k, а також кінцеві метрики відповіді (factuality, EM/ROUGE для QA).

- Виклики: hallucinations (LLM ігнорує або неправильно інтерпретує retrieved evidence), latency (cross-encoders), domain shift, оновлення індексу.

---

## Ключові висновки
- RAG дозволяє LLM бути "з'єднаним" з зовнішньою базою знань, що робить відповіді актуальнішими і більш обґрунтованими.
- Підходи до retrieval варіюються від простих лексичних (BM25) до складних dense, late-interaction і гібридних систем; на практиці часто застосовують кілька шарів (multistage).
- Якість retriever-а і reranker-а сильно впливає на кінцеву якість генерації; їх тренування (ICT, DPR, weak supervision) — важливий етап.

---

## Джерела
- "Retrieval-augmented generation" (локальний огляд, retrieval-augmented-generation.pdf) [local]
- Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. arXiv:2005.11401 [web]
- Aman A.I. Primer: "Retrieval Augmented Generation" — практичний посібник по pipeline і підходах до retrieval (онлайн) [web]


