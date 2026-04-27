# LLM-as-a-Judge (LLM як суддя)

## Executive Summary

LLM-as-a-Judge — підхід, у якому великі мовні моделі (LLM) використовуються як автоматичні оцінювачі ("судді") для оцінювання відповідей, резюме, перекладів, коду, токсичності тощо. Цей звіт узагальнює концепцію, методи, останні дослідження (2022–2026), репрезентативні емпіричні результати meta-evaluation, вразливості (adversarial attacks, bias), практичні шаблони застосування (prompt'и, pipeline), рекомендації з дизайну jury/ансамблів, оперативні оцінки вартості/латентності та governance/комплаєнс для високоризикових застосунків.

Ключові висновки:
- LLM-судді (особливо GPT‑4‑клас) демонструють значну, але варіабельну кореляцію з людськими оцінками по задачах (сумаризація, MT, QA, code), при цьому результати залежать від формату оцінки (comparative vs absolute), rubric'и і calibration.
- Найбільш надійні архітектури — ансамблі різнорідних суддів (jury), retrieval-augmented judges (RAG+judge) для фактчеку, та метрики/калібрування на gold-annotated наборах.
- Суттєві ризики: prompt-injection / universal adversarial phrases, self-bias (модель віддає перевагу стилю, близькому до свого тренувального корпусу), нестабільність при зміні версій і параметрів, та регуляторні вимоги у високоризикових доменах.
- Рекомендації: використовувати строгі рубрики (формальні шкали + приклади), фіксовані параметри inference (temperature ≈ 0), format validators (JSON schema), calibration на stratified gold sets, ensemble + escalation-to-human правила.

Цільова аудиторія: інженери ML/AI продуктів, дослідники NLP, відповідальні за модерацію/quality assurance, compliance-офіцери для high-risk доменів.

---

## Findings

### 1. Що таке "LLM-as-a-Judge"
- Сутність: LLM використовується як автоматичний оцінювач, який дає числові або категоріальні бали, ранжує варіанти або генерує rationale (обґрунтування). Підхід замінює / доповнює людські аннотації та традиційні поверхневі метрики (BLEU/ROUGE) більш семантично-чутливими оцінками.
- Вихідні формати: single numeric score, per-criterion sub-scores, pairwise comparative judgement, structured JSON з rationale та evidence.

### 2. Технічні архітектури
- Single judge: один потужний LLM (наприклад GPT‑4) оцінює кожний приклад.
- Jury / ensemble: кілька моделей (різних архітектур/розмірів) дають оцінки, які агрегуються (медіана, зважене усереднення, majority vote, rank-aggregation).
- RAG + Judge: спочатку витягуються релевантні документи (retriever), а далі LLM оцінює відповідність/фактичність на підставі підстави.

### 3. Де застосовується
- Summarization (consistency, factuality, coherence).
- Machine translation (adequacy, fluency) — як доповнення до COMET-подібних метрик.
- Open-ended QA (factuality, completeness).
- Code evaluation (correctness, robustness) — ensemble approaches показали приріст у кореляції з людьми.
- Toxicity/moderation (safety labels) — використовують як попередній фільтр або для паралельної розмітки.

### 4. Огляд ключових робіт (2022–2026)
Короткі релевантні джерела та їхні висновки:
- G‑Eval (Yang et al., 2023): GPT‑4 як backbone для NLG evaluation; показує підвищену узгодженість з людьми у низці задач (напр., сумаризація). URL: https://arxiv.org/abs/2303.16634
- GPTScore (Fu et al., NAACL 2024): інструкційно-орієнтований безреференсний скорер; демонструє гнучкість й добрі кореляції на численних датасетах. DOI: 10.18653/v1/2024.naacl-long.365 — https://aclanthology.org/2024.naacl-long.365/
- Self‑Refine / self-critique (Alon et al., 2023): ітеративні self-feedback методи підвищують якість генерації і застосовуються для оцінювання/rationale refinement. URL: https://arxiv.org/abs/2303.17651
- Adversarial attacks на LLM-оцінювачів (Raina et al., EMNLP 2024): показано вразливість до universal adversarial phrases і prompt‑injection; comparative scoring та sanitization — ефективні захисти. URL: https://aclanthology.org/2024.emnlp-main.427/
- COMET (Rei et al., 2020 / WMT): приклад task-specific fine-tuned neural metric для MT; служить baseline для порівняння з LLM‑оцінювачами. URL: https://arxiv.org/abs/2009.09025
- SE‑Jury (arXiv 2025): ансамбль для оцінки артефактів програмування, демонструє покращення кореляції з людьми порівняно з одиночними метриками. URL: https://arxiv.org/html/2505.20854v2

(Див. повний список джерел в розділі "Sources" в кінці.)

### 5. Репрезентативні емпіричні результати (meta-evaluation)
Примітка: числа залежать від dataset, task, розміру моделі та того, чи використовується comparative scoring. Нижче — репрезентативні інтервали з літератури:
- Summarization (G‑Eval / GPT‑4): Spearman ≈ 0.45–0.55 (instance-level залежно від датасету); system-level кореляції можуть бути вищими.
- Machine Translation: COMET (fine-tuned) — segment-level Spearman/Pearson ≈ 0.4–0.7; system-level Pearson / Kendall τ ≈ 0.8–0.95 (за результатами WMT‑type evaluations).
- QA / factuality: LLM‑evaluators показують Spearman ≈ 0.2–0.6 залежно від dataset та формату перевірки; RAG+judge підвищує достовірність перевірки фактів.
- Code: SE‑Jury та суміжні підходи повідомляють значне підвищення кореляції з людськими оцінками (відносні покращення десятки–сотні відсотків для деяких метрик); абсолютні Spearman/Cohen's Kappa — залежні від задачі і набору.
- Toxicity/moderation: Cohen's Kappa порівняно з людськими розмітками часто у межах 0.3–0.7 залежно від категорій та культури.

Рекомендація: завжди звітуйте мінімум дві метрики — rank-based (Spearman) та absolute/ICC/Cohen's Kappa або RMSE для абсолютних скорів; надавати segment- та system-level результати.

---

## Analysis / Comparison

### 1. Absolute vs Comparative scoring
- Absolute scoring (0–100; 1–5) простіший у зборі, але вразливіший до adversarial triggers і calibration drift.
- Comparative scoring (пара A vs B) більш стійкий до UA-фраз і часто дає кращу узгодженість із людськими судженнями для тонких відмінностей.
- Практика: використовувати comparative scoring там, де доступні парні варіанти; для absolute scoring — застосовувати жорстку calibration і validation.

### 2. Single judge vs Jury (ensemble)
- Single judge: дешевше, простіше; корисний як baseline. Ризики: model-specific bias і self‑narcissism.
- Jury: знижує variance, підвищує стійкість проти окремих model biases, особливо якщо включати diverse models (різні архітектури, розміри, fine-tuned specialists).
- Рекомендація: стартовий ensemble 3–5 суддів; зважене усереднення за calibration performance. Більші jury дають зростаючу витрату з федеративним прибутком, що зменшується.

### 3. RAG + Judge для фактчеку
- Retriever надає зовнішні джерела, які LLM має використовувати в rationale, що знижує hallucination у factuality checks.
- Відомі trade-offs: latency та вартість зростають; релевантність retrieval важлива (garbage-in → garbage-out).

### 4. Adversarial robustness comparison
- Best-of-breed defenses: comparative scoring + input sanitization + ensemble + anomaly detection.
- Adversarial training / surrogate testing продемонстрували зниження transferability UA-фраз, але не забезпечують абсолютного захисту.

### 5. Cost/latency trade-offs
- GPT‑4-class judges: висока точність, висока вартість, більша латентність.
- LLaMA‑class / distilled judges: низька вартість, нижча продуктивність, корисні для препроцесу/попередньої фільтрації.
- Практичні оптимізації: selective review (дорогі дзвінки лише для сумнівних випадків), batching, caching, distillation.

---

## Risks / Trade-offs

### Основні ризики
1. Adversarial manipulation: universal adversarial phrases і prompt injection можуть перекрутити результати оцінки.
2. Self‑bias / model favoritism: LLM‑оцінювачі можуть віддавати перевагу стилю, схожому до свого training distribution (особливо коли оцінювач і генератор однієї архітектури).
3. Вразливість до версій/параметрів: зміна версії моделі або temperature може змінити distribution оцінок.
4. Нестача експертизи: LLM не завжди мають експертну надійність у вузьких доменах; ризик неправомірних автозаключень.
5. Privacy / compliance: логування prompts/responses може зберігати PII; регуляторні вимоги (GDPR, EU AI Act та ін.) накладають обмеження.

### Trade-offs
- Точність vs вартість: кращі моделі дорожчі; ensemble → краща надійність за ціною збільшених ресурсів.
- Determinism vs uncertainty quantification: temperature=0 дає детерміністичність, але низьку оцінку невизначеності; n>1/ensemble дають розподіл, але дорожчі.
- Automation vs human oversight: повна автоматизація прискорює процес, але зменшує гарантії у high-stakes ситуаціях.

---

## Conclusion

LLM-as-a-Judge — перспективна і практично корисна технологія для масштабної оцінки NLG- і інших артефактів. Вона надає гнучкість, швидкість та семантичну глибину, але вимагає обережної інженерії (prompt design, calibration, ensemble), постійного adversarial‑testing та governance. Для production‑використання рекомендовано комбінувати automated LLM‑оцінки з людською перевіркою у випадках високого ризику, зберігати раціонали та версії моделей для аудиту, й імплементувати escalation rules.

Краткі практичні кроки впровадження:
1. Запустіть single-judge pipeline із deterministic параметрами і schema validation.
2. Зберіть stratified calibration gold set; проведіть calibration та визначте thresholds для ескалації.
3. Додайте jury (3–5 diverse judges) і RAG‑фактчек для fact‑sensitive tasks.
4. Впровадьте adversarial testing та input sanitization.
5. Налаштуйте logging/audit trails, retention policy та human-in-the-loop процедури для high-risk випадків.

---

## Sources

Основні джерела, згадані в звіті (URL/DOI):

- Yang, Zhi et al. "G‑Eval: NLG Evaluation using GPT‑4 with Better Human Alignment." arXiv 2023. https://arxiv.org/abs/2303.16634
- Fu, Jinlan; Ng, See‑Kiong; Jiang, Zhengbao; Liu, Pengfei. "GPTScore: Evaluate as You Desire." NAACL 2024 (Long). DOI: 10.18653/v1/2024.naacl-long.365. https://aclanthology.org/2024.naacl-long.365/
- Alon et al. "Self‑Refine: Iterative Refinement with Self‑Feedback." NeurIPS/2023 preprint. https://arxiv.org/abs/2303.17651
- Raina, Vyas; et al. "Is LLM‑as‑a‑Judge Robust? Investigating Universal Adversarial Attacks on Zero‑shot LLM Assessment." EMNLP 2024. https://aclanthology.org/2024.emnlp-main.427/
- Rei et al. "COMET: A Neural Framework for MT Evaluation." arXiv 2020. https://arxiv.org/abs/2009.09025
- SE‑Jury. "SE‑Jury: An LLM‑as‑Ensemble‑Judge Metric for Narrowing the Gap with Human Evaluation in SE." arXiv 2025. https://arxiv.org/html/2505.20854v2
- SummEval dataset (Fabbri et al., 2021): https://github.com/Yale-LILY/SummEval
- QAGS (factuality for summarization): https://github.com/ruotianluo/qags
- HumanEval (OpenAI): https://github.com/openai/human-eval
- MBPP (Mostly Basic Python Problems): https://github.com/google-research/google-research/tree/master/mbpp
- WMT data / MQM (translation human judgements): https://www.statmt.org/wmt-data/
- Jigsaw Toxic Comment dataset: https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data
- TruthfulQA: https://github.com/sylinrl/TruthfulQA
- MM‑Eval (multilingual meta‑evaluation benchmark), arXiv preprint (2024): https://arxiv.org/abs/2410.17578

Додаткові корисні матеріали (огляди, блоги):
- Arize blog — практичні поради щодо jury‑підходів та аудитів.

---

Якщо ви хочете, я можу:
- Надати повний розширений Markdown‑звіт із додатковими таблицями (кореляції по задачам з точними numeric values), детальними prompt‑шаблонами в JSON і псевдокодом у вигляді виконуваного Jupyter‑ноутбука.
- Згенерувати machine‑readable prompt templates (JSON) для single‑judge і jury pipelines.
- Підготувати експериментальний план та скрипти для reproducible meta‑evaluation на ваших наборах даних.

Будете зберегти цей звіт зараз (файл LLM_as_a_Judge_Report_UA.md)? Якщо збереження буде прийнято, воно буде зафіксоване. Якщо хочете правки — напишіть «REVISE:» і вкажіть секцію(ї), які треба змінити/додати.