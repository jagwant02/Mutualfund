import os
import json
from dotenv import load_dotenv

# Graceful degradation: If Chroma fails to compile due to Windows C++, we fall back to raw JSON
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

CHROMA_SERVER_HOST = os.environ.get("CHROMA_SERVER_HOST", "https://api.trychroma.com")
CHROMA_SERVER_PORT = os.environ.get("CHROMA_SERVER_PORT", "443")
CHROMA_API_KEY = os.environ.get("CHROMA_API_KEY", "")
CHROMA_TENANT = os.environ.get("CHROMA_TENANT", "default_tenant")
CHROMA_DATABASE = os.environ.get("CHROMA_DATABASE", "default_database")

COLLECTION_NAME = "mutual_funds_corpus"

def get_chroma_client():
    headers = {"X-Chroma-Token": CHROMA_API_KEY} if CHROMA_API_KEY else {}
    return chromadb.HttpClient(
        host=CHROMA_SERVER_HOST,
        port=CHROMA_SERVER_PORT,
        headers=headers,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE
    )

def fetch_top_k_chunks(query: str, k: int = 3, fund_filter: str = None) -> list[dict]:
    """
    If ChromaDB is installed, queries the cloud vector database.
    If not, it cleanly falls back to extracting JSON text directly from the data/raw folder.
    """
    if CHROMA_AVAILABLE:
        client = get_chroma_client()
        bge_embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-small-en-v1.5"
        )
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=bge_embeddings)
        where_clause = {"fund_name": fund_filter} if fund_filter else None
        results = collection.query(query_texts=[query], n_results=k, where=where_clause)
        
        chunks = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                chunks.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
        return chunks
    else:
        # [LOCAL MOCK FALLBACK FOR UI DEMONSTRATION]
        chunks = []
        raw_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "phase-03-data-ingestion", "data", "raw")
        if not os.path.exists(raw_dir): return chunks
        
        for filename in os.listdir(raw_dir):
            if filename.endswith(".json"):
                with open(os.path.join(raw_dir, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Basic string match heuristic
                q_lower = query.lower()
                if "hdfc" in q_lower and "hdfc" in data.get("amc", "").lower():
                    chunks.append({"text": data.get("raw_text", ""), "metadata": {"fund_name": data.get("fund_name"), "source_url": data.get("source_url"), "last_updated_date": data.get("last_updated_date")}})
                elif "nippon" in q_lower and "nippon" in data.get("amc", "").lower():
                    chunks.append({"text": data.get("raw_text", ""), "metadata": {"fund_name": data.get("fund_name"), "source_url": data.get("source_url"), "last_updated_date": data.get("last_updated_date")}})
                elif "nav" in q_lower or "sip" in q_lower:
                    # Return both if generic query
                    chunks.append({"text": data.get("raw_text", ""), "metadata": {"fund_name": data.get("fund_name"), "source_url": data.get("source_url"), "last_updated_date": data.get("last_updated_date")}})
                    
        return chunks[:k]

if __name__ == "__main__":
    # Rapid local debugging trigger
    print("Testing Vector Retrieval...")
    res = fetch_top_k_chunks("What is the expense ratio for HDFC Flexi Cap?")
    for item in res:
        print(f"\n[Score: {item['distance']}] Metadata: {item['metadata']}")
        print(f"Data: {item['text'][:100]}...")
