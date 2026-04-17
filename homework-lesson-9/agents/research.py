from langchain.agents import create_agent
from config import settings, RESEARCH_AGENT_PROMPT
from langchain.chat_models import init_chat_model
from fastmcp import Client
from mcp_utils import mcp_tools_to_langchain


llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

MAX_RESEARCH_INPUT = 3000  # chars — prevent huge gap lists from bloating the research request

async def research(request: str) -> str:
    async with Client(settings.search_mcp_url) as mcp_client:
        tools = await mcp_client.list_tools()
        lc_tools = mcp_tools_to_langchain(tools, mcp_client)

        agent = create_agent(
            model=llm,
            tools=lc_tools,
            system_prompt=RESEARCH_AGENT_PROMPT,
        )

        if len(request) > MAX_RESEARCH_INPUT:
            request = request[:MAX_RESEARCH_INPUT] + "\n\n[...truncated...]"

        result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request}]})

    return result["messages"][-1].content



# test
# if __name__ == "__main__":
#     result = asyncio.run(research("What are the key differences between langchain and langgraph?"))
#     print(result)

# python -m agents.research