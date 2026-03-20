from agent import agent
from config import Settings
settings = Settings()

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

        for chunk in agent.stream(
            {"messages": [("user", user_input)]},
            config=config
        ):
            
            if "agent" in chunk and "messages" in chunk["agent"]:
                for msg in chunk["agent"]["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        print(f"\nAgent: {msg.content}")


if __name__ == "__main__":
    main()
