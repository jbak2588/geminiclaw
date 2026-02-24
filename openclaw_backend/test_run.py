import os
from dotenv import load_dotenv
from agents.graph import team_graph

load_dotenv()

def run_test():
    # If API key is missing, prompt to set it but continue (it will fail later if actually called).
    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY is not set in environment.")

    print("=== Starting Agentic Team Test ===")
    
    initial_state = {
        "messages": [],
        "current_task": "Write a python function that calculates the nth Fibonacci number. It must include type hints and a docstring.",
        "reviewer_feedback": "",
        "status": "in_progress"
    }
    
    # We use stream to observe the steps the graph takes
    for event in team_graph.stream(initial_state):
        for key, value in event.items():
            print(f"\n--- Output from node: {key} ---")
            if "messages" in value and value["messages"]:
                last_msg = value["messages"][-1]
                print(last_msg.content)
            print(f"Current Status: {value.get('status')}")
            
    print("\n=== Workflow Completed ===")

if __name__ == "__main__":
    run_test()
