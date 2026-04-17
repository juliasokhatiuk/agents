import json
from unittest import result

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Server
from agents.planner import plan
from agents.research import research
from agents.critic import critique


acp_server = Server()

@acp_server.agent(name="planner", description="Agent that creates a research plan based on a user request.")
async def planner_handler(input: list[Message]) -> Message:
    user_text = input[-1].parts[0].content
   
    result = await plan(user_text) 

    return Message(role="agent",parts=[MessagePart(content=json.dumps(result))])



@acp_server.agent(name="researcher", description="Agent that conducts research based on the research plan and gathers findings.")
async def researcher_handler(input: list[Message]) -> Message:
    user_text = input[-1].parts[0].content
   
    result = await research(user_text) 

    return Message(role="agent", parts=[MessagePart(content=result)])



@acp_server.agent(name="critic", description="Agent that critiques the research results and provides feedback for improvement.")
async def critic_handler(input: list[Message]) -> Message:
    user_text = input[-1].parts[0].content
   
    result = await critique(user_text) 

    return Message(role="agent",parts=[MessagePart(content=json.dumps(result))])



ACP_PORT = 8903

if __name__ == "__main__":
    acp_server.run(port=ACP_PORT)
