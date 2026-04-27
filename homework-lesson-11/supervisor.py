from langchain.agents import create_agent
from tools import plan, research, critique, save_report
from config import settings
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langfuse import get_client

langfuse_client = get_client()

prompt = langfuse_client.get_prompt("supervisor", label="production")
system_prompt = prompt.compile(
    role="Supervisor agent orchestrating a multi-agent research system via the Plan → Research → Critique cycle"
)

llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

supervisor = create_agent(
    model=llm,
    tools=[plan, research, critique, save_report],
    system_prompt=system_prompt,
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"save_report": True}),
    ],
    checkpointer=MemorySaver(),
)
