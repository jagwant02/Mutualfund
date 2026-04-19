import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

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
    Embeds the user query using BAAI/bge-small-en-v1.5 and performs a semantic 
    cosine-similarity search against the remote ChromaDB collection.
    """
    client = get_chroma_client()
    
    # Utilizing exactly the same embedding dimensional space from Phase 4
    bge_embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=bge_embeddings
    )
    
    where_clause = None
    if fund_filter:
        where_clause = {"fund_name": fund_filter}
        
    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where_clause
    )
    
    # Flatten ChromaDB's complex dictionary response
    chunks = []
    if results["documents"] and len(results["documents"][0]) > 0:
        for i in range(len(results["documents"][0])):
            chunks.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })
            
    return chunks

if __name__ == "__main__":
    # Rapid local debugging trigger
    print("Testing Vector Retrieval...")
    res = fetch_top_k_chunks("What is the expense ratio for HDFC Flexi Cap?")
    for item in res:
        print(f"\n[Score: {item['distance']}] Metadata: {item['metadata']}")
        print(f"Data: {item['text'][:100]}...")
