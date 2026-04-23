import os
from dotenv import load_dotenv
from groq import Groq
from retriever import fetch_top_k_chunks

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# The 6 strict architecture constraints rigidly enforced via System Prompting
SYSTEM_PROMPT = """You are a strictly factual financial information assistant for Indian Mutual Funds.
You must adhere to the following absolute rules:
1. Answer relying ONLY on the provided context facts.
2. If the exact answer is not found in the context, you must reply: 'I do not have factual information on that topic in my current sources.'
3. Do not formulate any opinions, advice, or future speculations whatsoever. Check your output heavily for accidental bias.
4. The final response must not exceed 3 sentences.
5. You must include exactly ONE source web link based exclusively on the provided URL metadata.
6. You must append the exact string: 'Last updated from sources: <date>' to the bottom of your response, replacing <date> with the exact matching date found in the metadata.
"""

def generate_answer(user_query: str, fund_filter: str = None) -> str:
    """End-to-End RAG logic: Fetch context, build prompt, run Groq LLM inference."""
    
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        return "System Warning: GROQ_API_KEY is not configured in the root .env file."
        
    try:
        # Phase 5.1: Retrieve Dense Vectors from TryChroma
        retrieved_chunks = fetch_top_k_chunks(user_query, k=3, fund_filter=fund_filter)
        
        # Phase 5.2: Assemble Context Injection Block
        context_blocks = []
        latest_date = "Unknown"
        source_url = "Unknown"
        
        for chunk in retrieved_chunks:
            meta = chunk["metadata"]
            text = chunk["text"]
            context_blocks.append(f"FUND: {meta.get('fund_name')}\nFACTS: {text}")
            
            # Capture the first valid URL and Date for the footer citations algorithm
            if source_url == "Unknown" and meta.get("source_url"):
                source_url = meta.get("source_url")
            if latest_date == "Unknown" and meta.get("last_updated_date"):
                latest_date = meta.get("last_updated_date")
                
        compiled_context = "\n\n---\n\n".join(context_blocks)
        
        # Constructing the rigorous LLM generation payload
        user_payload = f"""
        CONTEXT CHUNKS FETCHED FROM VECTOR DATABASE:
        {compiled_context}
        
        METADATA REQUIRED FOR MANDATORY FOOTER:
        URL: {source_url}
        DATE: {latest_date}
        
        USER QUERY: {user_query}
        """
        
        # Phase 5.3: Execute LLM (Using Llama-3 via Groq for high-speed deterministic generation)
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Highly instruction-following open weight model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_payload}
            ],
            temperature=0.0, # Zero temperature to strictly enforce deterministic, factual responses
            max_tokens=200,  # Failsafe limit to prevent anything longer than 3 sentences physically rendering
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"System Error during LLM Generation Core: {e}"

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the exit load for HDFC Flexi Cap?"
    print(f"\nUser Query: {query}")
    print("-" * 60)
    print(generate_answer(query))
    print("-" * 60)
