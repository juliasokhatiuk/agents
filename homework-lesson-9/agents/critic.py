from langchain.agents import create_agent
from schemas import CritiqueResult
from config import settings, CRITIC_AGENT_PROMPT
from langchain.chat_models import init_chat_model
from fastmcp import Client
from mcp_utils import mcp_tools_to_langchain


llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

MAX_CRITIQUE_INPUT = 10000  # chars — enough to see the full report structure

async def critique(findings: str) -> CritiqueResult:
    async with Client(settings.search_mcp_url) as mcp_client:
        tools = await mcp_client.list_tools() 
        lc_tools = mcp_tools_to_langchain(tools, mcp_client)

        agent = create_agent(
            model=llm,
            tools=lc_tools,
            system_prompt=CRITIC_AGENT_PROMPT,
            response_format=CritiqueResult,
        )

        # Extract only the latest research block — strip any previously appended
        # critique feedback that the supervisor may have included in the findings string.
        marker = "=== LATEST RESEARCH ==="
        if marker in findings:
            latest = findings.split(marker)[-1].strip()
        else:
            latest = findings.strip()

        # Truncate to avoid exceeding context window
        if len(latest) > MAX_CRITIQUE_INPUT:
            latest = latest[:MAX_CRITIQUE_INPUT] + "\n\n[...truncated for length...]"

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": latest}]})

        return result["structured_response"].model_dump()
   


# test
# if __name__ == "__main__":
#     result = asyncio.run(critique("""Overview
# - LangChain: an open-source software framework (Python/JS) for building LLM applications (chains, agents, prompts, memory, retrievers, vectorstores, connectors, etc.). It’s primarily a developer library for composing LLM-based logic and experiments. 
# - LangGraph: a platform product (announced by the LangChain team as “LangGraph Platform”) for deploying, running and managing long‑running, stateful agents and agent workflows in production — includes an IDE, persistence, scaling, and production API 
# endpoints.

# Key information (concise)
# - Purpose
#   - LangChain: developer-facing framework & libraries for building LLM apps and agent logic.
#   - LangGraph: infrastructure/management layer to deploy, scale, and operate agents (production platform).
# - Scope
#   - LangChain: local/embedded code, modular primitives (LLM wrappers, prompts, chains, agents, memory, retrievers, vectorstores).
#   - LangGraph: runtime for long-running and stateful agent workloads, with a persistence layer, APIs, and an IDE (LangGraph Studio) for debugging and visibility.
# - Deployment & runtime
#   - LangChain: you run your code (locally, containers, your infra); has tools for deployment (e.g., LangServe) but is primarily a library.
#   - LangGraph: 1‑click deployment to production, horizontal scaling, durable execution for tasks that may be long or asynchronous, built-in endpoints for different interaction patterns.
# - State & durability
#   - LangChain: provides memory primitives and local approaches to state, but durability/scaling is left to your infra choices.
#   - LangGraph: provides a built-in persistence layer and infrastructure designed for durable conversational history, async collaboration and multi-agent workflows.
# - Product / licensing differences
#   - LangChain: free, open-source (MIT) framework and ecosystem.
#   - LangGraph: a managed platform product from the LangChain team (commercial/managed offering with platform features); the blog notes the product and related managed tooling.
# - Observability & tooling
#   - LangChain: ecosystem tools (e.g., LangSmith for observability/evaluation — note: LangSmith is a closed-source offering from the LangChain company).
#   - LangGraph: native Studio for debugging/visibility of deployed agents and production workflows.
# - When to choose which
#   - Use LangChain when you want to prototype, build, experiment or embed LLM logic in apps with full control over code and infra.
#   - Use LangGraph when you need production-grade deployment, long-running or stateful agents, built-in persistence, scalings, and easier operational tooling.

# Comparison / details (side-by-side summary)
# - Primary role
#   - LangChain = Builder library
#   - LangGraph = Runtime + managed platform
# - Typical developer workflow
#   - LangChain: write chains/agents locally → run/test → integrate into your app/infrastructure
#   - LangGraph: deploy agents to a managed runtime → use Studio and API endpoints to operate and scale
# - Complexity supported
#   - LangChain: general LLM workflows, sequential chains, agents
#   - LangGraph: long-running workflows, async/multi-agent collaboration, durable state, production reliability
# - Vendor/ops trade-offs
#   - LangChain: maximum flexibility and control; you manage infra, scaling, persistence.
#   - LangGraph: faster path to production and operational features, at the cost of using a managed platform (potential cost and vendor lock-in considerations).

# Key takeaways
# - They’re complementary: LangChain is the open-source framework for building LLM/agent logic; LangGraph is the platform to run and operate those (and similar) agents in production with durability, scaling, and tooling.
# - If you only need to build and iterate locally or manage your own infra, LangChain is the primary tool. If you need production deployment, long-running stateful agents, and operational conveniences, LangGraph (the LangChain team’s managed platform) 
# is designed for that gap.
# - Watch for product naming and commercial aspects (e.g., platform/observability components from the LangChain company can be 
# managed or closed-source).


# Sources
# - LangChain project/background (local knowledge base) — [local]
#   - langchain.pdf (notes: LangChain framework, LangSmith, LangGraph Platform launch date)
# - LangChain blog: “LangGraph Platform is now Generally Available: Deploy & manage long‑running, stateful Agents” — [web]     
#   - https://blog.langchain.com/langgraph-platform-ga/ (describes 1‑click deployment, API endpoints, persistence layer, LangGraph Studio, scaling)"""))

# print(result)

# python -m agents.critic

