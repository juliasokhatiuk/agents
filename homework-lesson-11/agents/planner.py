from langchain.agents import create_agent
from schemas import ResearchPlan
from tools import web_search, knowledge_search
from config import settings
from langchain.chat_models import init_chat_model
from langfuse import get_client

langfuse_client = get_client()

prompt = langfuse_client.get_prompt("planner_agent", label="production")
system_prompt = prompt.compile(
    role="research planning agent",
    task="to decompose the user's request into a high-level, actionable ResearchPlan schema",
    constraints="Avoid technical jargon, lengthy descriptions, or redundant instructions. The output must be a clean `ResearchPlan` object with no extra commentary.",
)


llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

planner_agent = create_agent(
    model=llm,
    tools=[web_search, knowledge_search],
    system_prompt=system_prompt,
    response_format=ResearchPlan,
)
