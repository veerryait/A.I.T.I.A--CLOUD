import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

# HF Space Persistent Storage Bridge
def is_huggingface_space() -> bool:
    """Detection for HF Spaces persistent storage environment"""
    return os.getenv("HF_SPACE") == "1" or os.path.exists("/data") or "SPACE_ID" in os.environ

if is_huggingface_space():
    os.environ["HF_SPACE"] = "1"
    HF_PERSIST_DIR = "/data/chroma"
else:
    HF_PERSIST_DIR = "./data/chroma"

class HybridLogStore:
    """
    ChromaDB embedded ( DuckDB + Parquet ) 
    Memory footprint: ~150MB for 10k logs
    """
    def __init__(self, persist_dir: str = HF_PERSIST_DIR):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Use Tiny model for M3 efficiency (22MB vs 400MB)
        print("Loading embedding model (~22MB)...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        
        # ChromaDB embedded configuration
        # Updated for ChromaDB 0.4.x compatibility where PersistentClient is preferred
        # but trying to respect user's Settings structure if possible, 
        # however 0.4.15 requires PersistentClient for persistence.
        try:
            self.client = chromadb.PersistentClient(path=persist_dir)
        except AttributeError:
             # Fallback for older versions if somehow installed, but we verified 0.4.15
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir,
                anonymized_telemetry=False
            ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="system_logs",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Vector store ready. Current count: {self.collection.count()}")
    
    def ingest_dataframe(self, df: pd.DataFrame, batch_size: int = 100):
        """Bulk ingest from pandas"""
        total = len(df)
        for i in range(0, total, batch_size):
            batch = df.iloc[i:i+batch_size]
            
            ids = [f"log_{row['timestamp']}_{idx}" for idx, row in batch.iterrows()]
            texts = batch['message'].tolist()
            
            # Metadata must be serializable (no numpy types)
            metadatas = []
            for _, row in batch.iterrows():
                meta = {
                    'service': str(row['service']),
                    'timestamp': str(row['timestamp']),
                    'level': str(row['level']),
                    'latency_ms': float(row['latency_ms']),
                    'error_count': int(row['error_count'])
                }
                metadatas.append(meta)
            
            # Generate embeddings
            embeddings = self.encoder.encode(texts, show_progress_bar=False).tolist()
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )
            
            if (i // batch_size) % 10 == 0:
                print(f"Ingested {i}/{total}...")
        
        # In 0.4.x, persistence is automatic with PersistentClient
        # self.client.persist() 
        print(f"Done. Total vectors: {self.collection.count()}")
    
    def query_similar_incidents(self, query_text: str, service: str = None, n=5) -> List[Dict]:
        """Semantic search + metadata filter"""
        try:
            where_filter = {"service": service} if service else None
            
            # Check how many items actually match the filter to avoid HNSW errors
            # Using get() with only ids to be fast
            matching_ids = self.collection.get(where=where_filter, include=[])['ids']
            count = len(matching_ids)
            
            n = min(n, count)
            if n == 0:
                print(f"No matching logs found for search in service: {service}")
                return []
                
            query_embedding = self.encoder.encode([query_text]).tolist()
            
            try:
                results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=n,
                    where=where_filter,
                    include=['metadatas', 'documents', 'distances']
                )
            except RuntimeError as e:
                if "contigious 2D array" in str(e) or "ef or M" in str(e):
                    print("HNSW Index too small/unstable. Falling back to plain GET.")
                    # Fallback: Just return the most recent matching logs
                    results = self.collection.get(
                        where=where_filter,
                        limit=n,
                        include=['metadatas', 'documents']
                    )
                    # Mock the query response structure
                    results['distances'] = [[0.5] * len(results['ids'])] 
                else:
                    raise e
            
            # Format results
            incidents = []
            if results['ids'] and len(results['ids']) > 0:
                # Handle cases where results['ids'] might be a 1D list from get() 
                # vs 2D list from query()
                ids = results['ids'][0] if isinstance(results['ids'][0], list) else results['ids']
                docs = results['documents'][0] if isinstance(results['documents'][0], list) else results['documents']
                metas = results['metadatas'][0] if isinstance(results['metadatas'][0], list) else results['metadatas']
                dists = results['distances'][0] if isinstance(results['distances'][0], list) else results['distances']

                for i in range(len(ids)):
                    incidents.append({
                        'id': ids[i],
                        'message': docs[i],
                        'metadata': metas[i],
                        'similarity_score': 1 - dists[i] if i < len(dists) else 0.5
                    })
            print(f"Search successful: found {len(incidents)} results for query '{query_text}'")
            return incidents
        except Exception as e:
            import traceback
            print(f"Search error details: {e}")
            traceback.print_exc()
            return []
    
    def get_recent_errors(self, minutes: int = 30) -> pd.DataFrame:
        """Get recent errors for contextual analysis"""
        # Since Chroma doesn't have native time filtering efficiently, we filter post-query
        # For production, use timestamp indexing in metadata
        results = self.collection.get(
            where={"error_count": {"$gte": 1}},
            include=['metadatas', 'documents']
        )
        
        if not results['ids']:
            return pd.DataFrame()
            
        df = pd.DataFrame([{
            'message': doc,
            **meta
        } for doc, meta in zip(results['documents'], results['metadatas'])])
        
        # Parse timestamps and filter
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return df[df['timestamp'] > cutoff]

    def flush_all_history(self):
        """Wipe all logs from the vector store"""
        try:
            self.client.delete_collection(name="system_logs")
            self.collection = self.client.get_or_create_collection(
                name="system_logs",
                metadata={"hnsw:space": "cosine"}
            )
            print("History flushed successfully.")
            return True
        except Exception as e:
            print(f"Flush error: {e}")
            return False

# Test
if __name__ == "__main__":
    store = HybridLogStore()
    if store.collection.count() == 0:
        df = pd.read_csv('data/raw/synthetic_logs.csv')
        store.ingest_dataframe(df)
    
    # Test query
    results = store.query_similar_incidents("timeout error", service="payment-db")
    print(f"\nFound {len(results)} similar incidents")
    for r in results[:2]:
        print(f"- {r['metadata']['service']}: {r['message']} (score: {r['similarity_score']:.2f})")
