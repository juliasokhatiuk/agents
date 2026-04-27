from langchain.agents import create_agent
from tools import web_search, knowledge_search, read_url
from config import settings
from langchain.chat_models import init_chat_model
from langfuse import get_client

langfuse_client = get_client()

prompt = langfuse_client.get_prompt("research_agent", label="production")
system_prompt = prompt.compile(
    role="Research Agent with access to both web search and a local knowledge base",
    task="to answer the user's question using tools and produce a structured Markdown report",
    constraints="Return only the final Markdown report.",
)

llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

research_agent = create_agent(
    model=llm,
    tools=[web_search, knowledge_search, read_url],
    system_prompt=system_prompt,
)