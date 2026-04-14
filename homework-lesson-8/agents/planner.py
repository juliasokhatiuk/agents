from langchain.agents import create_agent
from schemas import ResearchPlan
from tools import web_search, knowledge_search
from config import settings, PLANNER_AGENT_PROMPT
from langchain.chat_models import init_chat_model



llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

planner_agent = create_agent(
    model=llm,
    tools=[web_search, knowledge_search],
    system_prompt=PLANNER_AGENT_PROMPT,
    response_format=ResearchPlan,
)
