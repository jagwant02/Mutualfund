import os
import json
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration paths bridging Phase 3 and Phase 4
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "phase-03-data-ingestion", "data", "raw")
CHROMA_SERVER_HOST = os.getenv("CHROMA_SERVER_HOST", "https://api.trychroma.com") # Replace with exact trychroma URL
CHROMA_SERVER_PORT = os.getenv("CHROMA_SERVER_PORT", "443")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", "") # Inject trychroma auth key here
CHROMA_TENANT = os.getenv("CHROMA_TENANT", "default_tenant")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "default_database")

COLLECTION_NAME = "mutual_funds_corpus"

def load_documents():
    docs = []
    if not os.path.exists(RAW_DATA_DIR):
        print(f"Warning: Data directory {RAW_DATA_DIR} does not exist or has no files.")
        return docs
        
    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                docs.append(data)
    return docs

def chunk_text(text: str) -> list[str]:
    # Following strict Phase 4 Architecture limits
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)

def run_pipeline():
    print("Initiating Phase 4: Chunking & Embedding Pipeline...")
    
    # 1. Load Raw JSON Data
    documents = load_documents()
    if not documents:
        print("No documents found. Please ensure Phase 3 scraper has populated data/raw/.")
        return
    print(f"Loaded {len(documents)} source documents.")

    # 2. Configure BGE-Small Embedding Model
    # Using BAAI/bge-small-en-v1.5 natively through HuggingFace wrappers
    print("Loading embedding model: BAAI/bge-small-en-v1.5...")
    bge_embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5"
    )

    # 3. Initialize Remote ChromaDB Vector Store
    print(f"Connecting to remote ChromaDB at {CHROMA_SERVER_HOST}...")
    headers = {"X-Chroma-Token": CHROMA_API_KEY} if CHROMA_API_KEY else {}
    chroma_client = chromadb.HttpClient(
        host=CHROMA_SERVER_HOST,
        port=CHROMA_SERVER_PORT,
        headers=headers,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE
    )
    
    # Reset collection logic for cleanly reproducible indexing
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    except ValueError:
        pass # Collection didn't exist yet
        
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=bge_embeddings,
        metadata={"hnsw:space": "cosine"} # Calculating distance via Cosine Similarity
    )

    # 4. Chunk & Assemble Metadata Streams
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    chunk_counter = 0
    print("Chunking files and injecting structured metadata attributes...")
    
    for doc in documents:
        raw_text = doc.get("raw_text", "")
        if not raw_text.strip():
            continue
            
        chunks = chunk_text(raw_text)
        
        for i, chunk in enumerate(chunks):
            # Strict Metadata Wrap (critical for pre-retrieval filtering)
            meta = {
                "fund_name": doc.get("fund_name", "Unknown"),
                "source_url": doc.get("source_url", "Unknown"),
                "document_type": doc.get("document_type", "Webpage Content"),
                "last_updated_date": doc.get("last_updated_date", "Unknown"),
                "nav": doc.get("nav", "Data Unavailable"),
                "min_sip": doc.get("min_sip", "Data Unavailable"),
                "fund_size": doc.get("fund_size", "Data Unavailable"),
                "expense_ratio": doc.get("expense_ratio", "Data Unavailable"),
                "rating": doc.get("rating", "Data Unavailable"),
                "chunk_index": i
            }
            
            chunk_id = f"{doc.get('fund_name', 'default').replace(' ', '_')}_chunk_{i}"
            
            all_chunks.append(chunk)
            all_metadata.append(meta)
            all_ids.append(chunk_id)
            chunk_counter += 1

    # 5. Push generated vectors into ChromaDB SQLite file backend
    print(f"Pushing {chunk_counter} vectorized chunks into ChromaDB via BGE-Small...")
    collection.add(
        documents=all_chunks,
        metadatas=all_metadata,
        ids=all_ids
    )
    
    print(f"Embedding pipeline successful! Vectors durably written to remote ChromaDB at {CHROMA_SERVER_HOST}")

if __name__ == "__main__":
    run_pipeline()
