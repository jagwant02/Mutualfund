import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# --- Cross-Phase Architecture Routing ---
# By dynamically injecting these paths, the FastAPI server can seamlessly orchestrate
# logic written across the isolated phase folders into one cohesive network sequence.
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(ROOT_DIR, "phase-05-rag-engine"))
sys.path.append(os.path.join(ROOT_DIR, "phase-06-guardrails"))

from scrubber import scan_query
from generator import generate_answer

app = FastAPI(title="Mutual Fund Assistant MVP")

# Simple Request schema mapping
class ChatRequest(BaseModel):
    message: str

# ==========================================
# PHASE 7: The Backend Orchestration Network
# ==========================================

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_query = request.message.strip()
    
    print(f"> Processing incoming query: {user_query}")
    
    # Step 1: Input Guardrails Layer (Phase 6)
    # The Scrubber analyzes the raw text against compliance regex heuristics
    refusal_html = scan_query(user_query)
    
    if refusal_html:
        # A trigger phrase was caught. We instantly sever the connection to the DB
        # and LLM to absolutely guarantee zero financial advice is generated.
        print("> Blocked by Phase 6 Guardrails: Returning static AMFI refusal.")
        return {"response": refusal_html}
        
    # Step 2: Intelligence Layer (Phase 5)
    print("> Query Clean. Engaging Phase 5 RAG Engine (TryChroma + Groq)...")
    final_answer = generate_answer(user_query)
    
    return {"response": final_answer}

# ==========================================
# PHASE 8: The Dynamic Vanilla Frontend UI
# ==========================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mutual Fund Assistant | Facts Only</title>
    <!-- Google Fonts for Modern Typography -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; font-family: 'Inter', sans-serif; }
        body {
            margin: 0; background-color: #0f172a; color: #f8fafc;
            display: flex; flex-direction: column; height: 100vh;
            align-items: center; justify-content: center;
        }
        
        /* Premium Glassmorphism Interface Container */
        .chat-container {
            width: 100%; max-width: 650px; height: 85vh;
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px; display: flex; flex-direction: column;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }
        
        .chat-header {
            padding: 20px; background: rgba(15, 23, 42, 0.9);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;
        }
        .chat-header h1 { margin: 0; font-size: 1.25rem; font-weight: 600; color: #38bdf8; }
        .chat-header p { margin: 4px 0 0; font-size: 0.85rem; color: #94a3b8; }
        
        .chat-history {
            flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px;
        }
        
        .message { padding: 14px 18px; border-radius: 12px; max-width: 85%; font-size: 0.95rem; line-height: 1.5; }
        .message.user { align-self: flex-end; background: #38bdf8; color: #0f172a; font-weight: 500; }
        .message.bot { align-self: flex-start; background: #334155; border: 1px solid #475569; }
        .message.bot a { color: #38bdf8; }
        
        .loader { align-self: flex-start; margin-left: 10px; color: #94a3b8; font-size: 0.9rem; font-style: italic; display: none; }
        
        /* Clickable Suggested Queries Section */
        .suggestions {
            display: flex; gap: 10px; padding: 12px 24px;
            background: rgba(15, 23, 42, 0.4); flex-wrap: wrap; justify-content: center;
        }
        .pill {
            background: #1e293b; border: 1px solid #475569; color: #cbd5e1;
            padding: 6px 14px; border-radius: 20px; font-size: 0.8rem;
            cursor: pointer; transition: all 0.2s ease;
        }
        .pill:hover { background: #38bdf8; color: #0f172a; border-color: #38bdf8; }
        
        .input-area {
            padding: 20px 24px; border-top: 1px solid rgba(255, 255, 255, 0.05);
            display: flex; gap: 12px;
        }
        input {
            flex: 1; background: #1e293b; border: 1px solid #475569;
            color: white; padding: 14px 18px; border-radius: 8px; font-size: 0.95rem;
            outline: none; transition: border-color 0.2s;
        }
        input:focus { border-color: #38bdf8; }
        button {
            background: #38bdf8; color: #0f172a; border: none; padding: 0 24px;
            border-radius: 8px; font-weight: 600; cursor: pointer; transition: opacity 0.2s;
        }
        button:hover { opacity: 0.9; }
    </style>
</head>
<body>

<div class="chat-container">
    <div class="chat-header">
        <h1>Mutual Fund Intelligence</h1>
        <p>Verified Facts Only. Zero AI Speculation.</p>
    </div>
    
    <div class="chat-history" id="history">
        <div class="message bot">
            Hello! I am a compliant Mutual Fund assistant. I analyze verified AMC data to answer factual queries like Expense Ratios, NAVs, and Exit Loads. <b>I do not provide investment advice.</b> Ask me a question below.
        </div>
    </div>
    <div class="loader" id="loader">Computing across Vector Database...</div>
    
    <!-- Phase 8: Architecture Minimal UI clickables -->
    <div class="suggestions">
        <div class="pill" onclick="sendPill('What is the NAV for HDFC Flexi Cap?')">NAV for HDFC Flexi Cap?</div>
        <div class="pill" onclick="sendPill('What is the minimum SIP for Nippon India Growth?')">Min SIP for Nippon India?</div>
        <div class="pill" onclick="sendPill('Which fund should I invest in to make quick money?')">Should I invest in this? (Test Refusal)</div>
    </div>
    
    <div class="input-area">
        <input type="text" id="queryBox" placeholder="Ask a factual question..." onkeydown="if(event.key === 'Enter') sendQuery()">
        <button onclick="sendQuery()">Send</button>
    </div>
</div>

<script>
    // Pure Vanilla JS Logic communicating with the FastAPI layer
    const historyDiv = document.getElementById('history');
    const queryBox = document.getElementById('queryBox');
    const loader = document.getElementById('loader');

    function sendPill(text) {
        queryBox.value = text;
        sendQuery();
    }

    async function sendQuery() {
        const text = queryBox.value.trim();
        if (!text) return;
        
        // Append user node
        historyDiv.innerHTML += `<div class="message user">${text}</div>`;
        queryBox.value = '';
        historyDiv.scrollTop = historyDiv.scrollHeight;
        
        // Loader State
        loader.style.display = "block";
        
        try {
            // POST to the Phase 7 FastAPI endpoint we built
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            
            // Convert LLM line breaks into HTML breaks
            let formattedBotText = data.response.replace(/\\n/g, '<br>');
            
            // Append bot node
            historyDiv.innerHTML += `<div class="message bot">${formattedBotText}</div>`;
        } catch (error) {
            historyDiv.innerHTML += `<div class="message bot" style="color:#ef4444;">Server offline or configuring embeddings. Check console.</div>`;
        }
        
        loader.style.display = "none";
        historyDiv.scrollTop = historyDiv.scrollHeight;
    }
</script>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    # Injects the entire Phase 8 Frontend UI instantly into the browser!
    return HTML_TEMPLATE
