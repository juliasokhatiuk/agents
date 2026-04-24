from langchain.agents import create_agent
from tools import web_search, knowledge_search, read_url
from config import settings, RESEARCH_AGENT_PROMPT
from langchain.chat_models import init_chat_model


llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

research_agent = create_agent(
    model=llm,
    tools=[web_search, knowledge_search, read_url],
    system_prompt=RESEARCH_AGENT_PROMPT,
)