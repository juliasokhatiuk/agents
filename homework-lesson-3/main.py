from agent import agent
from config import Settings
settings = Settings()

def main():
    print("Research Agent (type 'exit' to quit)")
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
        
        for chunk in agent.stream(
            {"messages": [("user", user_input)]},
            config=config
        ):
            # print("CHUNK KEYS:", chunk.keys())
            # for key, val in chunk.items():
            #     print(f"  [{key}]:", val)

            if "model" in chunk and "messages" in chunk["model"]:
                for msg in chunk["model"]["messages"]:
            
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool in msg.tool_calls:
                            print(f"→ {tool['name']}({str(tool['args'])[:100]})")
            
                    if hasattr(msg, "content") and msg.content:
                        print(f"\nAgent: {msg.content.split('\n')[0]}")
        
       
if __name__ == "__main__":
    main()
