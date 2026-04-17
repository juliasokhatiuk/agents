from langchain.agents import create_agent
from schemas import ResearchPlan
from config import settings, PLANNER_AGENT_PROMPT
from langchain.chat_models import init_chat_model
from fastmcp import Client
from mcp_utils import mcp_tools_to_langchain


llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

async def plan(request: str) -> ResearchPlan:
    async with Client(settings.search_mcp_url) as mcp_client:
        tools = await mcp_client.list_tools()
        filtered_tools = [tool for tool in tools if tool.name in {"web_search", "knowledge_search"}]    
        lc_tools = mcp_tools_to_langchain(filtered_tools, mcp_client)

        agent = create_agent(
            model=llm,
            tools=lc_tools,
            system_prompt=PLANNER_AGENT_PROMPT,
            response_format=ResearchPlan,
        )

        result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request}]})

    return result["structured_response"].model_dump()
   


# test
# if __name__ == "__main__":
#     result = asyncio.run(plan("What are the key differences between langchain and langgraph?"))
#     print(result)

# python -m agents.planner