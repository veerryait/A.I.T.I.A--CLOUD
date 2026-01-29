import networkx as nx
import dowhy
import chromadb
import ollama
from fastapi import FastAPI
from prometheus_client import CollectorRegistry
import sys
import pandas as pd

def check_stack():
    print("🚀 Starting Stack Verification...\n")
    
    # 1. NetworkX & DoWhy
    try:
        G = nx.DiGraph()
        G.add_edge("Treatment", "Outcome")
        # Just verifying import and basic object creation works, deep dowhy usage requires data
        model = dowhy.CausalModel(
            data=pd.DataFrame({"Treatment": [0, 1], "Outcome": [0, 1]}),
            treatment="Treatment",
            outcome="Outcome",
            graph=G
        )
        print(f"✅ DoWhy + NetworkX: CausalModel initialized with {G.number_of_edges()} edge")
    except Exception as e:
        print(f"❌ DoWhy + NetworkX Failed: {e}")
        # import pandas as pd # Verify pandas if dowhy failed - REMOVED to fix scope error
        
    # 2. ChromaDB
    try:
        # Use a dummy embedding function to avoid downloading models during smoke test
        class DummyEmbeddingFunction:
            def __call__(self, input):
                # Return random vector of dim 384 (standard for generic models)
                import numpy as np
                return [np.random.rand(384).tolist() for _ in input]
                
        client = chromadb.Client()
        # Delete if exists to clean up previous failed runs
        try: client.delete_collection("smoke_test")
        except: pass
        
        collection = client.create_collection(
            name="smoke_test", 
            embedding_function=DummyEmbeddingFunction()
        )
        collection.add(documents=["hello world"], ids=["id1"])
        assert collection.count() == 1
        print("✅ ChromaDB: In-memory collection created and document added (with dummy embeddings)")
    except Exception as e:
        print(f"❌ ChromaDB Failed: {e}")

    # 3. Ollama
    try:
        # Check if service is reachable
        models = ollama.list()
        print(f"✅ Ollama: Connected! Found {len(models['models'])} models locally.")
    except Exception as e:
        print(f"⚠️  Ollama Warning: Could not connect to Ollama service. is 'ollama serve' running? Error: {e}")

    # 4. FastAPI & Prometheus
    try:
        app = FastAPI()
        registry = CollectorRegistry()
        print("✅ FastAPI + Prometheus: basic objects instantiated")
    except Exception as e:
        print(f"❌ FastAPI/Prometheus Failed: {e}")

    print("\n✨ Stack verification complete!")

if __name__ == "__main__":
    check_stack()
