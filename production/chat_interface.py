import os
import sys
from dotenv import load_dotenv

# Add this folder to Python's search path BEFORE other imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from session import SessionContext
from orchestrator import Orchestrator, MockNLUEngine, NLUEngine

# Load the .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def start_chat():
    print("--- Phase 4: Google MCP Integration Demo ---")
    
    # 1. Choose between Groq AI or Mock AI
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        print("Using Lightning-Fast Groq AI...")
        nlu = NLUEngine(api_key)
    else:
        print("No GROQ_API_KEY found in .env. Using Mock AI...")
        nlu = MockNLUEngine()
        
    orch = Orchestrator(nlu)
    ctx = SessionContext(session_id="user_123")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit": break
            
        response = orch.handle_message(user_input, ctx)
        print(f"Agent: {response}\n")

if __name__ == "__main__":
    start_chat()
