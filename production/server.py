import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from production.orchestrator import Orchestrator, MockNLUEngine
from production.nlu_engine import NLUEngine
from production.session import SessionContext, State
from dotenv import load_dotenv
import os

# Find the absolute path to the .env file in the production directory
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path) 

app = FastAPI()

# 1. Security (CORS) - Allows your website to talk to your server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup the Brain
try:
    nlu = NLUEngine()
    print("✅ Real NLU Engine Started (Groq)")
except Exception as e:
    print(f"⚠️ NLU Startup Warning: {e}. Using Mock AI Engine.")
    nlu = MockNLUEngine()

orch = Orchestrator(nlu)

# 3. Simple in-memory storage for User Sessions
# (In a big app, we would use a Database like Redis)
sessions = {}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serves the main website."""
    # Find the absolute path to static/index.html
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "static", "index.html")
    
    print(f"🔍 DEBUG: Attempting to serve index from: {index_path}")
    
    if not os.path.exists(index_path):
        print(f"❌ ERROR: index.html NOT FOUND at {index_path}")
        return HTMLResponse(content="<h1>Error: Home page file not found.</h1>", status_code=404)
        
    try:
        with open(index_path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"❌ ERROR: Could not read index.html: {e}")
        return HTMLResponse(content=f"<h1>Internal Error: {str(e)}</h1>", status_code=500)

@app.post("/chat")
async def chat(request: Request):
    """Receives user input from the website and returns AI response."""
    data = await request.json()
    user_text = data.get("text")
    session_id = data.get("session_id", "default")

    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = SessionContext(session_id=session_id)
    
    ctx = sessions[session_id]
    
    # Process message through our existing Orchestrator!
    response = orch.handle_message(user_text, ctx)
    
    return {
        "response": response,
        "state": ctx.state
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
