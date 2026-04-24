from langchain.agents import create_agent
from schemas import CritiqueResult
from tools import web_search, knowledge_search, read_url
from config import settings, CRITIC_AGENT_PROMPT
from langchain.chat_models import init_chat_model



llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

critic_agent = create_agent(
    model=llm,
    tools=[web_search, read_url, knowledge_search],
    system_prompt=CRITIC_AGENT_PROMPT,
    response_format=CritiqueResult,
)