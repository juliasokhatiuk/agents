from agent import run_agent, working_memory
from config import Settings
settings = Settings()

def main():
    print("Research Agent (type 'exit' to quit)")
    print("-" * 40)


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
        
        try:
            response_text = run_agent(user_input)
            
            print(f"\nAgent: {response_text}")
            
        except Exception as e:
            print(f" Error: {e}")

        
       
if __name__ == "__main__":
    main()
