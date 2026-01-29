from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from src.agents.controller import controller, LogEntry

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage controller lifecycle"""
    # Start controller in background
    asyncio.create_task(controller.start())
    yield
    controller.stop()

app = FastAPI(
    title="Causal Control Plane",
    description="Autonomous RCA with Local LLM",
    version="1.0.0",
    lifespan=lifespan
)

class LogSubmission(BaseModel):
    timestamp: str
    service: str
    level: str = "INFO"
    latency: float
    message: str

@app.post("/ingest/log")
async def ingest_log(log: LogSubmission):
    """Submit log for async processing"""
    entry = LogEntry(
        timestamp=datetime.fromisoformat(log.timestamp),
        service=log.service,
        level=log.level,
        latency=log.latency,
        message=log.message,
        metadata={}
    )
    await controller.submit_log(entry)
    return {"status": "queued", "queue_size": controller.raw_queue.qsize()}

@app.get("/graph/causal")
async def get_causal_graph():
    """Get current causal graph visualization data"""
    try:
        fig = controller.causal_engine.get_causal_graph_viz()
        return fig.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """System health and stats"""
    return {
        "processed_logs": controller.stats['processed'],
        "remediations": controller.stats['remediations'],
        "queue_depth": controller.raw_queue.qsize(),
        "vector_count": controller.memory.collection.count()
    }

@app.get("/remediations")
async def get_remediations():
    """Get history of AI actions"""
    return {"history": controller.remediation_history}

@app.delete("/remediations")
async def clear_remediations():
    """Clear AI action history"""
    controller.remediation_history = []
    return {"status": "cleared"}

@app.delete("/memory")
async def clear_memory():
    """Clear all logs and reset metrics"""
    # Clear ChromaDB
    try:
        # Get all IDs and delete them
        all_ids = controller.memory.collection.get()['ids']
        if all_ids:
            controller.memory.collection.delete(ids=all_ids)
    except:
        pass
    
    # Reset Controller
    controller.stats = {'processed': 0, 'errors': 0, 'remediations': 0}
    controller.remediation_history = []
    return {"status": "memory_wiped"}

@app.get("/query/similar")
async def query_similar(q: str, service: str = None, limit: int = 5):
    """Semantic search over logs"""
    results = controller.memory.query_similar_incidents(q, service, limit)
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    # Use 1 worker only (8GB constraint)
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1, loop="uvloop")
