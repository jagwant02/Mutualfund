import re

# Architecture Section 3.7: Strict heuristic blacklist to aggressively block advisory/opinions
BLACKLIST_REGEX = re.compile(
    r'\b(should i invest|recommend|recommendation|advice|advise|predict|forecast|better than|'
    r'which is better|buy|sell|allocate|portfolio|wealth|rich|opinion|'
    r'good investment|bad investment|future|outlook|returns in the future)\b',
    re.IGNORECASE
)

# Detect requests specifically asking for comparative performance or metric calculations
PERFORMANCE_REGEX = re.compile(
    r'\b(compare|performance over|historic return|roi|cagr calculated|which performed)\b',
    re.IGNORECASE
)

AMFI_LINK = "https://www.amfiindia.com/investor-corner"
HARD_REFUSAL_TEMPLATE = (
    "I am an MVP designed to provide only factual information. I cannot provide investment advice, "
    "opinions, or recommendations. You can learn more about safe mutual fund investments at the "
    f"<a href='{AMFI_LINK}' target='_blank' style='color:#3b82f6;text-decoration:underline;'>AMFI Investor Corner</a>."
)

def scan_query(query: str):
    """
    Scans the incoming user query. 
    Returns a refusal string if blocked.
    Returns None if the query is safe to pass to the RAG engine.
    """
    # 1. PII or Account Action blocks
    if re.search(r'\b\d{10}\b', query) or re.search(r'[A-Z]{5}\d{4}[A-Z]{1}', query):
         return "System Guardrail: Queries containing Account Numbers, Phone Numbers, or PAN details are strictly prohibited by our zero-PII security policy."
    
    # 2. Hard Advisory Refusals (Category 1)
    if BLACKLIST_REGEX.search(query):
        # Asynchronously we would log this event according to constraints, but we just return the template here
        return HARD_REFUSAL_TEMPLATE
        
    # 3. Performance Delegation (Category 2)
    if PERFORMANCE_REGEX.search(query):
        return (
            "I cannot output dynamic performance calculations or synthesize fund comparisons. "
            "Please refer strictly to the official AMC web links or factsheets for historical data."
        )
        
    # Clean Factual Query. Safe to proceed to the RAG LLM Context Loop.
    return None

if __name__ == "__main__":
    print(f"Test 1 (Safe): {scan_query('What is the nav for HDFC?')}")
    print(f"Test 2 (Advice): {scan_query('Which fund should I invest in?')}")
