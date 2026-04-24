import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Cross-Phase Architecture Routing ---
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(ROOT_DIR, "phase-05-rag-engine"))
sys.path.append(os.path.join(ROOT_DIR, "phase-06-guardrails"))

from scrubber import scan_query
from generator import generate_answer

app = FastAPI(title="Mutual Fund Assistant API")

# Enable CORS for Next.js development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for easier deployment, can be restricted later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def health_check():
    return {"status": "online", "message": "Mutual Fund API is active"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_query = request.message.strip()
    
    print(f"> Processing incoming query: {user_query}")
    
    # Step 1: Guardrails (Phase 6)
    refusal_html = scan_query(user_query)
    if refusal_html:
        return {"response": refusal_html}
        
    # Step 2: RAG Engine (Phase 5)
    final_answer = generate_answer(user_query)
    
    return {"response": final_answer}

