"""
Прості тести для кожного агента: planner, research, critic.
Кожен тест викликає агента з одним прикладом від юзера та перевіряє структуру відповіді.

Запуск: pytest test_agents.py -v
(з директорії homework-lesson-8)
"""

import logging
import os
import pytest
from dotenv import load_dotenv

# використовувати локальний кеш HF без перевірки оновлень
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("test_supervisor")


# ---------------------------------------------------------------------------
# Planner agent
# ---------------------------------------------------------------------------

def test_planner_agent():
    """Planner повертає ResearchPlan з валідними полями."""
    from agents.planner import planner_agent
    from schemas import ResearchPlan

    user_request = "What are the main differences between LangChain and LlamaIndex?"

    result = planner_agent.invoke({
        "messages": [{"role": "user", "content": user_request}]
    })

    plan: ResearchPlan = result["structured_response"]

    assert isinstance(plan, ResearchPlan), "Відповідь має бути екземпляром ResearchPlan"
    assert plan.goal, "goal не може бути порожнім"
    assert len(plan.search_queries) >= 1, "має бути хоча б 1 пошуковий запит"
    assert len(plan.sources_to_check) >= 1, "має бути хоча б 1 джерело"
    assert plan.output_format, "output_format не може бути порожнім"

    print(f"\n[planner] goal: {plan.goal}")
    print(f"[planner] queries: {plan.search_queries}")
    print(f"[planner] sources: {plan.sources_to_check}")
    print(f"[planner] format: {plan.output_format}")


# ---------------------------------------------------------------------------
# Research agent
# ---------------------------------------------------------------------------

def test_research_agent():
    """Research agent повертає непорожній Markdown-звіт."""
    from agents.research import research_agent

    user_request = "What is retrieval-augmented generation (RAG) and how does it work?"

    result = research_agent.invoke({
        "messages": [{"role": "user", "content": user_request}]
    })

    report: str = result["messages"][-1].content

    assert isinstance(report, str), "Відповідь має бути рядком"
    assert len(report) > 100, "Звіт надто короткий — очікується розгорнута відповідь"

    print(f"\n[research] перші 300 символів звіту:\n{report[:300]}")


# ---------------------------------------------------------------------------
# Critic agent
# ---------------------------------------------------------------------------

def test_critic_agent():
    """Critic agent повертає CritiqueResult з verdict APPROVE або REVISE."""
    from agents.critic import critic_agent
    from schemas import CritiqueResult

    # Мінімальний приклад "досліджень" від юзера
    sample_findings = """
    # RAG Overview

    Retrieval-Augmented Generation (RAG) combines a retrieval system with a generative model.
    Documents are indexed in a vector store; at query time, relevant chunks are fetched and
    passed as context to the LLM, which generates a grounded answer.

    Sources:
    - https://arxiv.org/abs/2005.11401 (Lewis et al., 2020)
    """

    result = critic_agent.invoke({
        "messages": [{"role": "user", "content": sample_findings}]
    })

    critique: CritiqueResult = result["structured_response"]

    assert isinstance(critique, CritiqueResult), "Відповідь має бути екземпляром CritiqueResult"
    assert critique.verdict in ("APPROVE", "REVISE"), "verdict має бути APPROVE або REVISE"
    assert isinstance(critique.is_fresh, bool)
    assert isinstance(critique.is_complete, bool)
    assert isinstance(critique.is_well_structured, bool)
    assert isinstance(critique.strengths, list)
    assert isinstance(critique.gaps, list)
    assert isinstance(critique.revision_requests, list)

    print(f"\n[critic] verdict: {critique.verdict}")
    print(f"[critic] fresh={critique.is_fresh}, complete={critique.is_complete}, structured={critique.is_well_structured}")
    print(f"[critic] strengths: {critique.strengths}")
    print(f"[critic] gaps: {critique.gaps}")


# ---------------------------------------------------------------------------
# Supervisor (full pipeline: plan → research → critique → save_report + HITL)
# ---------------------------------------------------------------------------

def test_supervisor():
    """
    Supervisor проходить повний цикл plan→research→critique→save_report.
    Коли supervisor зупиняється на HITL-interrupt (save_report), тест
    автоматично відповідає 'approve' і перевіряє, що звіт збережено.
    """
    from supervisor import supervisor
    from langgraph.types import Command
    import uuid

    user_request = (
        "Compare RAG approaches: naive, sentence-window, and parent-child. "
        "Write a report."
    )

    config = {
        "configurable": {"thread_id": f"test-supervisor-{uuid.uuid4()}"},
        "recursion_limit": 50,  # кожен tool call = 2 кроки (agent + tools node)
    }

    # Відображення назви інструменту → назва агента, що викликається
    TOOL_TO_AGENT = {
        "plan": "planner_agent",
        "research": "research_agent",
        "critique": "critic_agent",
        "save_report": "save_report (HITL)",
    }

    collected_tokens = []
    interrupted = False
    seen_chunk_types = set()

    print("=== Supervisor: старт (прохід 1) ===", flush=True)
    print(f"Запит: {user_request}", flush=True)

    # Перший прохід: supervisor працює до interrupt на save_report
    for chunk in supervisor.stream(
        {"messages": [{"role": "user", "content": user_request}]},
        config=config,
        stream_mode=["updates", "messages"],
        version="v2",
    ):
        chunk_type = chunk.get("type")
        seen_chunk_types.add(chunk_type)

        if chunk_type == "messages":
            token, _ = chunk["data"]
            if token.content:
                collected_tokens.append(token.content)

        elif chunk_type == "updates":
            data = chunk["data"]
            for node_name, node_data in data.items():
                if node_name == "__interrupt__":
                    interrupted = True
                    print("[INTERRUPT] supervisor waiting for save_report approval", flush=True)
                    log.info("[INTERRUPT] supervisor waiting for save_report approval")
                elif node_name == "tools":
                    tool_msgs = node_data.get("messages", [])
                    for msg in tool_msgs:
                        tool_name = getattr(msg, "name", None)
                        if tool_name:
                            agent_label = TOOL_TO_AGENT.get(tool_name, tool_name)
                            print(f"[TOOL] {tool_name:<15} -> {agent_label}", flush=True)
                            log.info("[TOOL] %-15s -> %s", tool_name, agent_label)
                else:
                    print(f"[NODE] {node_name}", flush=True)
                    log.info("[NODE] %s", node_name)

        else:
            log.debug("unknown chunk type=%r keys=%s", chunk_type, list(chunk.keys()))

    print(f"Типи чанків у першому проході: {seen_chunk_types}", flush=True)
    assert interrupted, (
        f"Supervisor мав зупинитись на HITL interrupt перед збереженням звіту. "
        f"Типи чанків що прийшли: {seen_chunk_types}"
    )

    # Другий прохід: авто-approve → supervisor зберігає файл
    print("=== Supervisor: auto-approve (pass 2) ===", flush=True)
    final_tokens = []
    for chunk in supervisor.stream(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        stream_mode=["updates", "messages"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_name, node_data in chunk["data"].items():
                if node_name == "tools":
                    tool_msgs = node_data.get("messages", [])
                    for msg in tool_msgs:
                        tool_name = getattr(msg, "name", None)
                        if tool_name:
                            agent_label = TOOL_TO_AGENT.get(tool_name, tool_name)
                            print(f"[TOOL] {tool_name:<15} -> {agent_label}", flush=True)
                            log.info("[TOOL] %-15s -> %s", tool_name, agent_label)
                elif node_name != "__interrupt__":
                    print(f"[NODE] {node_name}", flush=True)
                    log.info("[NODE] %s", node_name)
        elif chunk["type"] == "messages":
            token, _ = chunk["data"]
            if token.content:
                final_tokens.append(token.content)

    full_output = "".join(collected_tokens + final_tokens)

    assert len(full_output) > 100, "Supervisor мав згенерувати змістовний вивід"
    log.info("=== Supervisor: завершено ===")
    log.info("Перші 400 символів виводу:\n%s", full_output[:400])
