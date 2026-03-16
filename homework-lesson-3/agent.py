from config import Settings, SYSTEM_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from tools import web_search, read_url, write_report
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent


settings = Settings()

llm = ChatOpenAI(
    api_key=settings.api_key.get_secret_value(),
    model=settings.model_name
)


tools = [web_search, read_url, write_report]


memory = MemorySaver()


agent = create_agent(
    model=llm, 
    tools=tools, 
    system_prompt=SYSTEM_PROMPT,
    checkpointer=memory
    )