from supervisor import supervisor
from config import settings
from langgraph.types import Command
import os
from dotenv import load_dotenv
import uuid

load_dotenv()


def stream_tokens(chunks):
    """Print LLM tokens from a supervisor stream."""
    for chunk in chunks:
        if chunk["type"] == "messages":
            token, _ = chunk["data"]
            if token.content:
                print(token.content, end="", flush=True)


def resume_supervisor(decision: dict, config: dict):
    """Resume supervisor after HITL interrupt with the given decision."""
    stream_tokens(supervisor.stream(
        Command(resume={"decisions": [decision]}),
        config=config,
        stream_mode=["updates", "messages"],
        version="v2",
    ))


def main():
    print("Multi-agent research system (type 'exit' to quit)")
    print("-" * 40)

    session_id = str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": session_id},
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

                
        # Stream agent progress and LLM tokens until interrupt
        
        interrupted = False
        chunks = supervisor.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            stream_mode=["updates", "messages"],
            version="v2",
        )

        for chunk in chunks:
            if chunk["type"] == "messages":
                token, _ = chunk["data"]
                if token.content:
                    print(token.content, end="", flush=True)
            elif chunk["type"] == "updates" and "__interrupt__" in chunk["data"]:
                interrupted = True
                print(f"\n\nInterrupt: {chunk['data']['__interrupt__']}")

        if not interrupted:
            print("\nSupervisor finished without interrupt.")
            continue  # повертаємось до наступного запиту

        user_action = input("Enter action (approve/edit/reject): ").strip().lower()

        # Resume with streaming after human decision
        if user_action == "approve":
            resume_supervisor({"type": "approve"}, config)

        elif user_action == "edit":
            feedback = input("Enter feedback for revision: ").strip()
            resume_supervisor({"type": "reject", "message": f"REVISE: {feedback}"}, config)

        elif user_action == "reject":
            reason = input("Reason for rejection: ")
            resume_supervisor({"type": "reject", "message": reason}, config)

        else:
            print("Unknown action. Valid: approve / edit / reject")
            continue

if __name__ == "__main__":
    main()
