from langchain.agents import create_agent
from langchain_core.tools import tool
from config import settings, SUPERVISOR_PROMPT
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware

from fastmcp import Client
from acp_sdk.client import Client as ACPClient
from acp_sdk.models import Message, MessagePart

import asyncio

llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

# ── ACP helpers ───────────────────────────────────────────────────────────────

async def _call_acp(agent_name: str, text: str) -> str:
    async with ACPClient(base_url=settings.acp_url,  headers={"Content-Type": "application/json"}) as client:
        result = await client.run_sync(
            [Message(role="user", parts=[MessagePart(content=text)])],
            agent=agent_name,
        )
        return result.output[-1].parts[0].content
    
# ── Tools (обгортки над ACP) ──────────────────────────────────────────────────

@tool
def plan(request: str) -> str:
    """Generate a structured research plan based on the user's request."""
    return asyncio.run(_call_acp("planner", request))


@tool
def research(request: str) -> str:
    """Research a topic using local knowledge and web sources."""
    return asyncio.run(_call_acp("researcher", request))


@tool
def critique(findings: str) -> str:
    """Critically evaluate the research findings and suggest improvements."""
    return asyncio.run(_call_acp("critic", findings))    



@tool
def save_report(filename: str, content: str) -> str:
    """Saves the final research report as a Markdown file."""
    async def save_report_mcp(filename: str, content: str) -> str:
        async with Client(settings.report_mcp_url) as client:
            result = await client.call_tool("save_report", {"filename": filename, "content": content})
            return str(result)
    return asyncio.run(save_report_mcp(filename, content))



supervisor = create_agent(
    model=llm,
    tools=[plan, research, critique, save_report],
    system_prompt=SUPERVISOR_PROMPT,
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"save_report": True}),
    ],
    checkpointer=MemorySaver(),
)
