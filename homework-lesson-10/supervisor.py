
from langchain.agents import create_agent
from tools import plan, research, critique, save_report
from config import settings, SUPERVISOR_PROMPT
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware


llm = init_chat_model(settings.model_name, api_key=settings.api_key.get_secret_value())

supervisor = create_agent(
    model=llm,
    tools=[plan, research, critique, save_report],
    system_prompt=SUPERVISOR_PROMPT,
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"save_report": True}),
    ],
    checkpointer=MemorySaver(),
)
