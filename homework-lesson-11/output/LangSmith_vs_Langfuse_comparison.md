# LangSmith vs Langfuse — LLM Observability Platforms

## Executive Summary

This report compares LangSmith (LangChain’s observability, evaluation, and deployment product) and Langfuse (an open-core LLM observability / LLM engineering platform) across features, integrations, deployment options, security/compliance, pricing & retention, operational concerns, and recommended user profiles. It summarizes where each product is strongest and highlights areas that require vendor confirmation before purchase (notably BYOK/KMS support, definitive Langfuse-managed SOC2 artifacts, and up-to-date public pricing snapshots).

Short recommendations:
- Choose LangSmith when you want a LangChain-native, managed SaaS with built-in agent/deployment workflows, turnkey alerting, and vendor-managed compliance (SOC2/HIPAA claims), and you accept a closed-source vendor model.
- Choose Langfuse when you need open-core self-hosting, ClickHouse-backed high-volume analytics, deep extensibility, or strict data sovereignty. Note: some enterprise features are in the repo’s ee/ (enterprise) paths and require a commercial EE license.

## Findings

1) Platform overviews
- LangSmith (LangChain)
  - Purpose: Observability, evaluation, and deployment product from LangChain supporting agent traces and LangChain-native workflows.
  - Offered as managed SaaS and Enterprise self-host/hybrid add-ons. Built to integrate tightly with LangChain and LangGraph tooling.
  - Notable feature: Polly assistant (AI insights), built-in alerting, workspace & trace management.
  - Sources: LangSmith docs & LangChain pricing and changelog.

- Langfuse
  - Purpose: Open-core LLM engineering & observability platform (trace logging, prompt management, evals, datasets), designed for self-host or managed cloud usage.
  - Architecture: ClickHouse for analytics, Postgres for metadata, Redis for queues, object storage for artifacts.
  - Key differentiator: MIT-licensed core (root LICENSE) with an ee/ directory governed by an enterprise license for additional features.
  - Sources: Langfuse GitHub, docs repo, ClickHouse partner page.

2) Integrations & SDKs
- LangSmith
  - Official SDKs: Python, JavaScript/TypeScript, Go, Java, plus LangGraph SDKs (docs list these languages). [LangSmith reference]
  - Integrations: First-class LangChain integrations, many LLM providers via LangChain (OpenAI, Anthropic etc.), agent frameworks (LangChain, LangGraph, OpenAI agents, etc.). [LangSmith integrations]

- Langfuse
  - Official SDKs: Python and JavaScript/TypeScript SDKs; OpenAPI spec / typed SDKs for custom clients. [Langfuse README]
  - Integrations: OpenTelemetry (OTEL) ingestion, LangChain, LlamaIndex, OpenAI SDKs; provider-agnostic by design (local models are supported via instrumented frameworks). [Langfuse docs]

Notes & caveats: Some integration claims (e.g., exact set of supported provider SDKs and which SDKs implement which capabilities such as automatic trace capture) should be validated in each product’s SDK docs and example repos prior to integration work.

3) Licensing & deployment
- LangSmith: commercial closed-source SaaS; Enterprise plan offers hybrid/self-hosted deployment options (contact sales). [LangSmith self-hosted & pricing]
- Langfuse: open-core — core components under MIT Expat (root LICENSE), with ee/ directories governed by a Langfuse Enterprise license (ee/LICENSE). You can self-host the MIT core; EE components require a commercial license. [Langfuse LICENSE, ee/LICENSE]

4) Security & compliance
- LangSmith
  - Public claims: SOC 2 Type II, HIPAA capability (BAA available on Enterprise), GDPR compliance, EU data region options, enterprise SSO/OIDC, RBAC, audit logs (Enterprise feature). [LangSmith changelog & Regions FAQ; audit logs doc]
  - Data residency and DPA likely available through Enterprise contracts.

- Langfuse
  - Langfuse Cloud (managed) is presented on partner pages (ClickHouse) as SOC2/ISO27001/GDPR compliant; self-hosted customers must manage infrastructure security (encryption-at-rest, TLS, backups, IAM). Open-source core requires the operator to configure and maintain security controls. Enterprise-only features (RBAC, audit logs) may live in ee/ and require a commercial license. [Langfuse docs, ClickHouse page, ee/LICENSE]

Caveat: While LangSmith has explicit SOC2 announcement in their changelog, Langfuse-managed compliance artifacts (SOC2/ISO attestation) should be requested from Langfuse sales/trust pages for confirmation.

5) Pricing & retention
- LangSmith
  - Published LangChain pricing shows Developer, Plus, and Enterprise tiers with included trace quotas (Developer/Plus small included trace volumes) and pay-as-you-go overages. Enterprise includes self-host/hybrid options. Retention controls and workspace TTLs exist; extended retention is Enterprise-gated. [LangChain pricing; LangSmith retention docs]

- Langfuse
  - Open-source core: free to self-host (infrastructure costs apply).
  - Managed tiers (docs/pricing.md): Hobby (free) and paid Core/Pro/Enterprise plans with increasing quotas, retention, and SLA features. Self-hosted retention configuration relies on object storage and periodic deletion jobs; ClickHouse sizing drives infra cost. [langfuse-docs pricing.md; data retention docs]

Important: Exact current prices, included quotas, overage rates, and retention durations should be validated at time of purchase (pricing pages change frequently). For both vendors, enterprise features (long retention, audit logs, SSO) are often gated behind Enterprise plans.

6) Deployment & operations
- LangSmith
  - Enterprise self-host/hybrid option exists; contact sales for self-hosted deployment artifacts. LangSmith uses a managed service by default; self-hosting is an Enterprise add-on. [LangSmith self-hosted docs]

- Langfuse
  - Self-hosting: Helm charts and docker-compose examples are available; recommended production stack includes ClickHouse cluster, Postgres, Redis, and object storage (S3 or MinIO).
  - ClickHouse sizing: community guidance suggests starting with a small 3-node ClickHouse cluster (e.g., 2 vCPU, ~8 GiB each) for low-volume use and scaling horizontally for higher throughput; exact sizing depends on ingestion rate, payload size, and retention window. Backups and snapshot guidance documented in self-hosting backups docs. [langfuse docs; GH discussions; ClickHouse page]

Operational note: Running Langfuse at scale requires ClickHouse expertise; managed Langfuse or ClickHouse Cloud can reduce ops burden.

7) Alerting & integrations
- LangSmith: built-in alerting on trace/metric thresholds with notification channels including webhooks, Slack, PagerDuty, and email; alerts configured in the UI and use workspace secrets for integration keys. [LangSmith alerts doc]
- Langfuse: supports webhooks and Slack integrations (prompt management webhooks). Being OTEL-enabled, Langfuse supports export-based workflows to external alerting systems; metric-threshold alerts in UI may be gated to Pro/Enterprise — verify on Langfuse-managed pricing/features pages. [Langfuse webhooks doc; OTEL notes]

8) Operational security features
- RBAC, SSO/OIDC, audit logs: Both vendors provide enterprise-grade SSO and RBAC flows; LangSmith documents audit logging retention and Enterprise gating; Langfuse provides SSO and RBAC but some audit features are EE (enterprise) gated. [LangSmith audit logs; langfuse auth & audit docs]
- Encryption & KMS: Managed offerings claim encryption in transit and at rest. Explicit customer-managed key (BYOK) support should be confirmed with vendors — not conclusively found in public docs during this research. (Action: confirm with vendor sales/trust pages.)

## Analysis / Comparison (side-by-side)

- Openness & license
  - LangSmith: closed-source SaaS with Enterprise self-host options. Vendor-controlled.
  - Langfuse: open-core; MIT core + EE components under commercial license. Self-hostable and auditable.

- Integration & language support
  - LangSmith: Multiple official SDKs (Python/JS/Go/Java) and first-class LangChain integrations—best fit for LangChain-first teams.
  - Langfuse: Python & JS SDKs plus OpenAPI; OTEL-first design makes it provider-agnostic and easy to plug into many stacks.

- Deployment & control
  - LangSmith: SaaS-first; Enterprise self-host/hybrid available for customers requiring data residency.
  - Langfuse: Self-host-first (Helm/Docker), managed option available—better for teams that want full control.

- Scalability & cost
  - LangSmith: pay-as-you-go SaaS — easier ops but potentially higher recurring costs at high volume.
  - Langfuse: ClickHouse backend is cost-effective at scale for analytic workloads, but requires ops expertise and infrastructure cost management.

- Security & compliance
  - LangSmith: publicly claims SOC2 Type II and HIPAA capability; Enterprise features for BAAs and extended retention.
  - Langfuse: managed offering claims enterprise compliance via partner pages; self-hosted customers are responsible for controls. EE features may be required for audit logs and advanced RBAC.

- Alerting & integrations
  - LangSmith: richer built-in alerting and notification channels out-of-the-box.
  - Langfuse: supports webhooks and OTEL export; native metric-threshold alerts in UI require feature/plan confirmation.

- Extensibility
  - LangSmith: extensible within the LangChain ecosystem; better turnkey integration for LangChain agents.
  - Langfuse: extensible and forkable; can modify source, add integrations, and adapt ClickHouse schema for custom analytics.

## Risks & Trade-offs

- Vendor lock-in vs control
  - LangSmith: easier to adopt but more vendor control over data and feature availability; enterprise self-host options mitigate but are gated.
  - Langfuse: self-hosting gives maximum control but increases operations and maintenance overhead.

- Compliance validation
  - LangSmith publishes compliance claims and enterprise contractual options; Langfuse-managed compliance claims should be validated with vendor-provided SOC2/ISO artifacts before procurement.

- Operational cost & expertise
  - Langfuse at scale requires ClickHouse expertise. Under-provisioned clusters can lead to ingestion/backlog problems; over-provisioning increases cost.

- Enterprise feature gating
  - Both platforms gate long-term retention, audit logs, and advanced RBAC under enterprise or EE features; ensure required features are included in contract.

## Conclusion

Both LangSmith and Langfuse are strong choices for LLM observability, but they target slightly different buyer needs:
- LangSmith: Best for teams invested in LangChain who want an integrated SaaS-first experience with built-in alerting, agent management, and vendor-managed compliance. Consider LangSmith when you want minimal ops overhead and close integration with LangChain agents.
- Langfuse: Best for teams that need open-source freedom, self-host control, and cost-effective analytics at scale via ClickHouse. Consider Langfuse when you want to own infrastructure, require deep extensibility, or operate under strict data residency requirements.

Caveats: Before final procurement, validate the following with vendors:
- Current pricing tiers, included quotas, and overage costs (pricing pages update frequently).
- Langfuse-managed compliance artifacts (SOC2/ISO27001) if you rely on Langfuse Cloud for compliance.
- BYOK / customer-managed key support for encryption at rest on managed offerings.
- Exact alerting capabilities and any plan gating for metric/threshold alerting in Langfuse managed.
- Enterprise license details for Langfuse ee/ components and what features are covered.

## Sources

- LangSmith / LangChain
  - LangSmith reference (SDKs): https://docs.langchain.com/langsmith/reference
  - LangSmith integrations: https://docs.langchain.com/langsmith/integrations
  - LangSmith pricing (LangChain pricing): https://www.langchain.com/pricing
  - LangSmith self-hosted overview: https://docs.langchain.com/langsmith/self-hosted
  - LangSmith data purging / retention: https://docs.langchain.com/langsmith/data-purging-compliance
  - LangSmith audit logs: https://docs.langchain.com/langsmith/audit-logs
  - LangSmith SOC 2 announcement: https://changelog.langchain.com/announcements/langsmith-is-now-soc-2-type-ii-compliant
  - LangSmith SDK GitHub (langsmith-sdk): https://github.com/langchain-ai/langsmith-sdk

- Langfuse
  - Langfuse GitHub (README): https://github.com/langfuse/langfuse
  - Langfuse root LICENSE (MIT + ee note): https://github.com/langfuse/langfuse/blob/main/LICENSE
  - Langfuse ee/LICENSE (Enterprise license): https://github.com/langfuse/langfuse/blob/main/ee/LICENSE
  - Langfuse docs repo: https://github.com/langfuse/langfuse-docs
  - Langfuse pricing (docs override): https://github.com/langfuse/langfuse-docs/blob/main/md-override/pricing.md
  - Langfuse data retention doc: https://github.com/langfuse/langfuse-docs/blob/main/content/docs/administration/data-retention.mdx
  - Langfuse backups (self-hosting): https://github.com/langfuse/langfuse-docs/blob/main/content/self-hosting/configuration/backups.mdx
  - Langfuse webhooks / Slack integrations: https://github.com/langfuse/langfuse-docs/blob/main/content/docs/prompt-management/features/webhooks-slack-integrations.mdx
  - Langfuse ClickHouse partner page: https://clickhouse.com/docs/cloud/features/ai-ml/langfuse
  - Langfuse community sizing discussion: https://github.com/langfuse/langfuse/discussions/5924
  - Langfuse Helm / k8s community repo: https://github.com/langfuse/langfuse-k8s


---

Notes
- This report was compiled from vendor documentation, GitHub repos, and partner pages. Some items (KMS/BYOK support, current pricing snapshots, and managed compliance attestations for Langfuse Cloud) require direct vendor confirmation. If you approve, I will finalize and save this report under the provided filename. If you request revisions, start your reply with "REVISE:" followed by the section(s) to change and I will update the report accordingly.