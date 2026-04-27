# Prompt Caching для оптимізації вартості і продуктивності

## Executive Summary
Коротко: Prompt Caching (включно з caching prefill / past_key_values — KV/PKV, ембеддінгами та відповіями) може знизити вартість inference і покращити latency. Найбільш вигідні сценарії — повторювані/шаблонні запити, великі статичні контексти (довгі документи) та self-hosted рантайми, що дозволяють повторно використовувати внутрішні KV. Для production-рішень рекомендовано комбінувати multi-tier кеш (L1 local LRU + L2 Redis + L3 vector DB / object storage), використовувати zstd+fp16/int8 для blob-компресії, додати singleflight/stale-while-revalidate для захисту від stampede, та впровадити метрики/SLO і KMS-шифрування. Нижче — детальний практичний посібник, включно з серіалізаційним форматом (Protobuf), псевдокодом, спостережуваністю, cost-model та планом міграції.

---

## Findings (Що та як кешувати)
1. Що кешувати
- Full LLM outputs (класичне response cache) — просте, ефективне для повторюваних запитів.
- Prompt templates + precomputed context chunks (recommended default): кешуйте оброблені chunks/summary, вставляйте змінні на льоту.
- Embeddings per chunk / query — обов'язково кешувати у векторній БД та hot-cache (Redis) для швидкого RAG.
- past_key_values (KV/prefill blobs) — дуже ефективні, але доступні переважно при self-hosted рантаймах (vLLM, custom Triton setups).
- Partial token outputs / streaming chunks — корисно для швидкого TTFT при streaming APIs.

2. Key design best-practices
- Нормалізація запиту: trim, NFKC, sort key-value pairs, маскування non-deterministic полів.
- Хешування: SHA256(normalized) для довгих prompt'ів.
- Включати model_id, tokenizer_version, template_version, params (temperature, top_p, max_tokens) у простір імен.
- Для персоналізації додавайте tenant_id/user_id або зберігайте персональний кеш окремо з коротким TTL.
- Використовуйте HMAC на blob для запобігання підміни.

3. Архітектура
- Multi-tier: L1 in-process LRU (fastest) → L2 Redis cluster (hot) → L3 object store (S3) + vector DB (ANN) для embeddings.
- Для KV blobs використовувати Redis (string/blob) або object store + Redis pointer, залежно від розміру blob.
- Для hot embeddings використовувати Redis з LRU/TTL, та vector DB для повноцінного пошуку.

---

## Analysis / Implementation Details
1. Serialization schema (Protobuf) — RECOMMENDED
- Protobuf схема (example):

syntax = "proto3";
package llmcache;

message KVBlobMeta {
  string model_name = 1;
  string model_version = 2;
  string tokenizer_id = 3;
  string dtype = 4; // "fp16"/"fp32"/"int8"
  repeated int32 layer_shapes = 5; // flattened shapes or per-layer tokens
  uint64 created_at = 6; // epoch ms
  uint32 ttl_seconds = 7;
  string source_hash = 8; // sha256 of canonicalized prompt
  string schema_version = 9; // e.g., "kv-v1"
  string key_id = 10; // KMS key id used for encryption
  bytes signature = 11; // HMAC signature
}

message KVBlob {
  KVBlobMeta meta = 1;
  bytes payload = 2; // compressed bytes (zstd)
}

- Usage: сериалізувати KVBlob, підписати HMAC(meta+payload), зашифрувати payload envelope через KMS data key.

2. Compression & storage
- Compress: zstd level 3 for low-latency, 6–9 for better ratio on background writes.
- Quantize: store tensors as fp16 or int8 where supported. Use post-quantization lib if available.
- Max blob: impose 16–64 MB limit. Shard large prefill into chunked KV per chunk_id.
- Storage strategy: store encrypted KVBlob in Redis only if blob size < 1–4MB; для більших зберігати у object store і в Redis зберігати pointer + metadata.

3. Stampede mitigation (pseudocode summarized)
- Singleflight + Redis setnx + pubsub + stale-while-revalidate. Serve stale entry while refresh in background with probabilistic early-refresh.
- Use short lock TTL and ensure leader computes and publishes completion on channel.

4. Embedding migration strategy
- Maintain per-embedding version tags: emb:v1, emb:v2.
- Dual-read: query v2 first; fallback to v1 if partial results.
- Lazy re-embed: schedule background re-embed per doc upon access.
- Bulk migration option: queue batched re-embed jobs and build new index in parallel (dual-index swap).

5. Chunking heuristics
- Defaults: chunk_size = 512–1024 tokens; overlap = 10–25% (use 20% default).
- For summarization/hierarchical RAG: paragraph-level (128–512 tokens) + chunk-level (512–1024 tokens) + section summaries.
- Token budget: ensure sum(context_tokens) + expected_response_tokens <= model_max_context.

6. Vector DB tuning
- HNSW: start with M=32, efConstruction=200, tune efSearch at runtime for p95 latency/recall target.
- IVF+PQ for large corpora: nlist ~ sqrt(N) heuristic; nprobe runtime=5–32; test recall drop.
- Keep hot-top-K in Redis for fastest access; use pubsub to sync updates.

7. Observability and SLOs
- Metrics to export (Prometheus names):
  - cache_prefill_hits_total
  - cache_prefill_misses_total
  - cache_prefill_hit_rate (derived)
  - prefill_get_latency_seconds_bucket
  - prefill_compress_seconds, prefill_decompress_seconds
  - prefill_blob_size_bytes
  - prefill_evictions_total
  - prefill_singleflight_waits_total
  - embed_migration_queue_depth
- Alerts / SLO examples:
  - SLO: 99% of hot cache reads < 50 ms
  - Alert if hit_rate < 75% over 5m window for top-1k keys
  - Alert if prefill_evictions_rate > threshold or eviction spikes
- Tracing: instrument read->decompress->verify->use as spans; tag with model_id/template_id/key_hash.

8. Security & compliance (concrete)
- In-transit: TLS 1.2+/mutual TLS for internal services; enforce network policies.
- At-rest: envelope encryption. Example: generate data_key via KMS; AES-GCM encrypt payload; store encrypted_data_key alongside object; rotate wrapping key periodically.
- HMAC: use tenant-scoped HMAC key; on read verify HMAC(meta+payload).
- RBAC: per-namespace Redis users + network segmentation; per-tenant KMS keys for strict isolation.
- PII: detect/redact PII before caching (PII-detector pipeline). Personal responses: TTL <= 1 hour unless consent and encryption policy allow more.
- Compliance: keep audit log for writes/reads: who, when, key_id, size, operation.

9. Concurrency & consistency
- Use write-through for strong consistency: on update write to source-of-truth and update cache within same transactional flow (or via event with strong ordering and versioning).
- Use CAS (ETag/version) to avoid races. Redis WATCH/MULTI/EXEC example included in pseudocode below.
- Event-driven invalidation: publish doc:update events; subscribers invalidate and optionally re-embed.

---

## Risks / Trade-offs
- Storage costs vs hit-rate: high-granularity caching (per-param) increases storage and management overhead. Use analytic-driven selection of keys to cache (top N queries, hottest chunks).
- Staleness: cached answers may become wrong after source updates — mitigate via TTL, versioning, and event-driven invalidation.
- Provider limits: hosted LLM APIs typically do not expose past_key_values — cannot realize maximum KV savings without self-hosting.
- Security/Compliance: storing sensitive user content increases regulatory burden; apply strict TTLs, encryption, and audit.
- Complexity: managing multi-tier caches, migrations, and ANN indexes adds operational complexity. Start small and iterate.

---

## Concrete Examples & Pseudocode
1) Redis response cache (template + params)

```python
# canonicalize, hash, include model/params
key = f"resp:v{TEMPLATE_V}:m={MODEL}:h={sha256(canonical_prompt)}:t={temp}"
val = {"response": output_text, "created_at": ts, "model": MODEL}
# on read
resp = redis.get(key)
if resp:
    return resp
else:
    output = call_llm(prompt, params)
    redis.set(key, serialize(val), ex=TTL)
    return output
```

2) Singleflight lock + background refresh (Redis)

```python
def get_prefill(key):
    entry = redis.hgetall(key)
    if entry and not expired(entry):
        return entry.value
    # Try lock
    if redis.setnx("lock:"+key, instance_id, ex=LOCK_TTL):
        val = compute_prefill(key)
        redis.set(key, serialize(val), ex=TTL)
        redis.publish("ready:"+key, "1")
        redis.delete("lock:"+key)
        return val
    else:
        # wait pubsub or poll
        wait_for_pubsub_or_timeout("ready:"+key, 5)
        return redis.get(key)
```

3) Embedding dual-read + lazy re-embed

(see section 5 in Findings)

---

## Cost-model worked example (practical)
Assumptions:
- requests/day = 10,000
- hit_rate = 40% (4,000)
- avg_saved_tokens = 150 tokens per hit
- token_price = $0.0004 per token (example) => saved $0.06 per hit
- Redis monthly cost = $300
- Storage: avg_blob = 0.5 MB, N_blobs = 10,000 => 5 GB => $0.50/month (S3 cheap)

Daily saving = 4000 * $0.06 = $240/day => ~$7,200/month
Net monthly saving ≈ $7,200 - ($300+0.5) ≈ $6,899.5

Sensitivity:
- If hit_rate falls to 25% => daily saving = 2500 * 0.06 = $150/day => $4500/month => still often net-positive.
- Use this template plugging real token prices, avg_saved_tokens, and infra costs.

---

## Conclusion
Prompt caching (templates, embeddings, KV/prefill) provides значні економічні і latency-переваги, особливо при self-hosted рантаймах. Головні практичні кроки: почати з template+chunk-level caching, впровадити multi-tier архітектуру, захистити дані через KMS+HMAC, ввести singleflight і stale-while-revalidate, і мати чітку стратегію для міграції ембеддінгів. Інструментальний набір: Redis (hot cache), vector DB (ANN index), object storage (для великих blob), observability (Prometheus/Grafana) та KMS. Для початку я рекомендую підготувати PoC: vLLM + Redis LMCache + Qdrant (3-node) з інструментами моніторингу — я можу згенерувати docker-compose/k8s manifests і Prometheus/Grafana dashboards під цей PoC.

---

## Sources
(вибрані посилання, 2022–2026)
- Redis Labs — Get faster LLM inference and cheaper responses with LMCache and Redis: https://redis.io/blog/get-faster-llm-inference-and-cheaper-responses-with-lmcache-and-redis/
- vLLM — Automatic Prefix Caching: https://docs.vllm.ai/en/latest/design/prefix_caching/
- OpenAI — Streaming API responses: https://developers.openai.com/api/docs/guides/streaming-responses
- Pinecone docs: https://www.pinecone.io/docs/
- Milvus docs: https://milvus.io/docs/
- Qdrant docs: https://qdrant.tech/documentation/
- Weaviate docs: https://weaviate.io/developers/weaviate
- Anthropic API docs: https://www.anthropic.com/docs
- Google Vertex AI generative models docs: https://cloud.google.com/vertex-ai/docs
- LangChain integrations: https://langchain.readthedocs.io/

---

Appendix: Next steps I can do for you (choose any):
- Generate reproducible PoC (docker-compose or k8s) for vLLM + Redis + Qdrant.
- Produce Prometheus+Grafana dashboards JSON and sample alert rules.
- Produce Terraform to provision Redis cluster + object store + KMS policy.
- Provide detailed QA/test plan and sample unit/integration tests.

