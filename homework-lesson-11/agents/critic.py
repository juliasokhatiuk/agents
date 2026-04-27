from langchain.agents import create_agent
from schemas import CritiqueResult
from tools import web_search, knowledge_search, read_url
from config import settings
from langchain.chat_models import init_chat_model
from langfuse import get_client

langfuse_client = get_client()

prompt = langfuse_client.get_prompt("critic_agent", label="production")
system_prompt = prompt.compile(
    role="research critic agent",
    task="audit a research result, not to trust it by default",
    constraints="Be strict, concise, and evidence-based. Output only a valid `CritiqueResult` object.",
)


llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

critic_agent = create_agent(
    model=llm,
    tools=[web_search, read_url, knowledge_search],
    system_prompt=system_prompt,
    response_format=CritiqueResult,
)