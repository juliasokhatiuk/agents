from urllib import response
import json
from config import Settings, SYSTEM_PROMPT
# from langchain_openai import ChatOpenAI
# from langchain_core.tools import tool
# from langchain.agents import create_agent
# from langgraph.checkpoint.memory import MemorySaver

from tools import (
    web_search, read_url, write_report,
    web_search_tool_schema, read_url_tool_schema, write_report_tool_schema)


settings = Settings()

from openai import OpenAI

client = OpenAI(api_key=settings.api_key.get_secret_value())


TOOLS_MAP = {
    "web_search": web_search,
    "read_url": read_url,
    "write_report": write_report,
}

TOOLS_SCHEMA = [web_search_tool_schema, read_url_tool_schema, write_report_tool_schema]

working_memory = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def run_agent(user_input: str):

    working_memory.append({"role": "user", "content": user_input})

    for i in range(settings.max_iterations):
        
        response = client.responses.create(
            model=settings.model_name,
            input=working_memory,              
            tools=TOOLS_SCHEMA,
        )
    
        working_memory.extend(response.output)
    
        tool_calls = [item for item in response.output if item.type == "function_call"]

        if not tool_calls:
            # Якщо інструментів немає — це фінальна відповідь для користувача
            final_msg = next((item for item in response.output if item.type == "message"), None)
            return final_msg.content[0].text if final_msg else "Done."

        for call in tool_calls:
                func = TOOLS_MAP[call.name]
                args = json.loads(call.arguments)

                # args_str = ", ".join([f'{k}="{v}"' for k, v in args.items()])
                # print(f"\n🔧 Tool call: {call.name}({args_str})")
                
                # Виклик (тут вже повертається текст <= 5000 символів)
                result = func(**args) 
                log_tool_call(call.name, args, result)
                
                # preview = str(result)[:100].replace('\n', ' ')
                # print(f"📎 Result: {preview}...")

                # Додаємо результат у список повідомлень
                working_memory.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": str(result),
                })
                

    else:
        print(f"Stopped after step limit: {settings.max_iterations}")


def log_tool_call(name: str, args: dict, result):
    log_args = {k: (v[:50] + "..." if k == "content" else v) for k, v in args.items()}
    args_str = ", ".join([f'{k}="{v}"' for k, v in log_args.items()])
    print(f"\n🔧 Tool call: {name}({args_str})")

    if name == "web_search":
        count = len(result) if isinstance(result, list) else str(result).count('"title"')
        print(f"📎 Result: Found {count} results...")

    elif name == "read_url":
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                content = parsed.get("content", result)
            except:
                content = result
        else:
            content = str(result)
        print(f"📎 Result: [{len(content)} chars] {content[:80].replace(chr(10), ' ')}...")

    elif name == "write_report":
        short = str(result).replace("Report successfully saved to ", "")
        short_path = "/".join(short.replace("\\", "/").split("/")[-2:])
        print(f"📎 Result: Report saved to {short_path}")

    else:
        print(f"📎 Result: {str(result)[:100]}...")