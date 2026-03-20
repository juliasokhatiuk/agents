from agent import agent
import json
from config import Settings
settings = Settings()

def log_tool_call(name: str, args: dict, result):
    log_args = {k: (v[:50] + "..." if k == "content" else v) for k, v in args.items()}
    args_str = ", ".join([f'{k}="{v}"' for k, v in log_args.items()])
    print(f"\n🔧 Tool call: {name}({args_str})")

    if name == "knowledge_search":
        try:
            parsed = json.loads(result)
            docs = parsed.get("results", [])
            print(f"📎 Result: [{len(docs)} documents found]")
            for doc in docs[:3]:
                filename = doc.get("file", "unknown")
                page = doc.get("page", "?")
                snippet = doc.get("content", "")[:80].replace("\n", " ")
                print(f"   - 📄 {filename} (Page {page}): {snippet}...")
        except (json.JSONDecodeError, AttributeError):
            print(f"📎 Result: {str(result)[:100]}...")
    
    elif name == "web_search":
        count = str(result).count('"title"')
        # count = len(result) if isinstance(result, list) else str(result).count('"title"')
        print(f"📎 Result: Found {count} results...")

    elif name == "read_url":
        try:
            parsed = json.loads(result)
            content = parsed.get("content", str(result))
        except (json.JSONDecodeError, AttributeError):
            content = str(result)
        print(f"📎 Result: [{len(content)} chars] {content[:80].replace(chr(10), ' ')}...")

    elif name == "write_report":
        short = str(result).replace("Report successfully saved to ", "")
        short_path = "/".join(short.replace("\\", "/").split("/")[-2:])
        print(f"📎 Result: Report saved to {short_path}")

    else:
        print(f"📎 Result: {str(result)[:100]}...")




def main():
    print("Research Agent with RAG (type 'exit' to quit)")
    print("-" * 40)

    config = {"configurable": {"thread_id": "my_chat_session_1"},
              "recursion_limit": settings.max_iterations
              }

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        pending_tool_calls = {}

        for chunk in agent.stream(
            {"messages": [("user", user_input)]},
            config=config
        ):
            
            # if "agent" in chunk and "messages" in chunk["agent"]:
            #     for msg in chunk["agent"]["messages"]:
            #         if hasattr(msg, "content") and msg.content:
            #             print(f"\nAgent: {msg.content}")
            
            if "agent" in chunk:
                for msg in chunk["agent"]["messages"]:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            pending_tool_calls[tc["id"]] = {"name": tc["name"], "args": tc["args"]}
                    elif hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
                        print(f"\nAgent: {msg.content}")

            # Логуємо результати
            if "tools" in chunk:
                for msg in chunk["tools"]["messages"]:
                    tool_id = getattr(msg, "tool_call_id", None)
                    if tool_id and tool_id in pending_tool_calls:
                        call = pending_tool_calls.pop(tool_id)
                        log_tool_call(call["name"], call["args"], msg.content)


if __name__ == "__main__":
    main()
