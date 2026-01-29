import asyncio
from asyncio import Queue, QueueFull
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import json
import logging

from src.causal.discovery import CausalDiscoveryEngine
from src.models.memory import HybridLogStore
from src.models.llm_client import LocalDiagnostician

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Controller")

@dataclass
class LogEntry:
    timestamp: datetime
    service: str
    level: str
    latency: float
    message: str
    metadata: Dict

class AsyncRCAController:
    """
    Async architecture for memory efficiency on M3 8GB
    - No threading overhead (single event loop)
    - Bounded queues prevent OOM
    - Streaming processing
    """
    def __init__(self, max_queue_size=100):
        self.raw_queue = Queue(maxsize=max_queue_size)      # Ingestion -> Analysis
        self.action_queue = Queue(maxsize=50)               # Analysis -> Action
        
        # Components (initialized once, shared)
        self.causal_engine = CausalDiscoveryEngine()
        self.memory = HybridLogStore()
        self.diagnostician = LocalDiagnostician()
        
        self._running = False
        self.stats = {
            'processed': 0,
            'errors': 0,
            'remediations': 0
        }
        self.remediation_history = []  # Store last 20 actions
        
    async def start(self):
        """Start all coroutines"""
        self._running = True
        logger.info("Starting Async Controller...")
        
        # Run all loops concurrently
        await asyncio.gather(
            self._ingestion_loop(),
            self._analysis_loop(),
            self._action_loop(),
            self._monitoring_loop()
        )
    
    def stop(self):
        """Graceful shutdown"""
        self._running = False
        logger.info("Controller stopping...")
    
    async def submit_log(self, log_entry: LogEntry):
        """External API submits here"""
        try:
            self.raw_queue.put_nowait(log_entry)
        except QueueFull:
            logger.warning("Raw queue full, dropping log (backpressure)")
    
    # Private Loops
    async def _ingestion_loop(self):
        """Stage 1: Enrich and embed"""
        while self._running:
            try:
                log = await asyncio.wait_for(self.raw_queue.get(), timeout=1.0)
                
                # Async-compatible embedding (run in executor to not block)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._sync_ingest,
                    log
                )
                
                self.raw_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Ingestion error: {e}")
    
    def _sync_ingest(self, log: LogEntry):
        """Synchronous ChromaDB interaction (thread-safe)"""
        try:
            self.memory.collection.add(
                ids=[f"{log.timestamp.isoformat()}_{log.service}"],
                embeddings=[self.memory.encoder.encode([log.message])[0].tolist()],
                metadatas=[{
                    'service': log.service,
                    'timestamp': log.timestamp.isoformat(),
                    'level': log.level,
                    'latency': log.latency,
                    'error_count': 1 if log.level == "ERROR" else 0 
                }],
                documents=[log.message]
            )
            self.stats['processed'] += 1
        except Exception as e:
            logger.error(f"Sync ingest failed: {e}")
    
    async def _analysis_loop(self):
        """Stage 2: Causal analysis + LLM diagnosis"""
        while self._running:
            await asyncio.sleep(2)  # Analyze every 2 seconds
            
            # Check for anomalies in recent data
            # Run in executor because Chroma get is sync
            recent_errors = await asyncio.get_event_loop().run_in_executor(
                None, self.memory.get_recent_errors, 5  # Last 5 minutes
            )
            
            if len(recent_errors) > 3:  # Threshold for investigation
                logger.info(f"Anomaly detected: {len(recent_errors)} recent errors")
                
                # Get causal context (synchronous, CPU-bound)
                context = await self._build_context(recent_errors)
                
                # LLM Diagnosis (async, GPU-bound)
                diagnosis = await self.diagnostician.diagnose(context)
                
                if diagnosis['confidence_score'] > 0.8:
                    await self.action_queue.put({
                        'type': 'remediate',
                        'action': diagnosis['recommended_action'],
                        'target': diagnosis['affected_service'],
                        'reason': diagnosis['root_cause']
                    })
    
    async def _build_context(self, error_df: pd.DataFrame) -> Dict:
        """Build rich context for LLM"""
        # Most affected service
        svc_counts = error_df['service'].value_counts()
        if svc_counts.empty:
            return {}
        target_svc = svc_counts.index[0]
        
        # Query similar past incidents
        similar = await asyncio.get_event_loop().run_in_executor(
            None,
            self.memory.query_similar_incidents,
            "connection timeout",  # Generic error pattern
            target_svc,
            3
        )
        
        # Rebuild causal model with recent data if needed (expensive, cache it)
        if not hasattr(self, '_cached_model') or self.stats['processed'] % 500 == 0:
            # Safely getting all data for rebuild could be heavy, 
            # optimized for example purposes
            all_data = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: pd.DataFrame([m for m in self.memory.collection.get()['metadatas']]) if self.memory.collection.count() > 0 else pd.DataFrame()
            )
            if len(all_data) > 100:
                self.causal_engine.build_model(all_data)
                self._cached_model = True
        
        causal_estimate = self.causal_engine.estimate.value if self.causal_engine.estimate else 0.0
        
        # Dynamic Causal Chain based on service and data
        if "db" in target_svc:
            chain = f"db_contention -> pool_wait -> latency (ATE: {causal_estimate:.2f})"
        elif "cache" in target_svc:
            chain = f"cache_miss/overload -> latency -> errors"
        elif "gateway" in target_svc:
            chain = f"ingress_load -> upstream_timeout -> errors"
        else:
            chain = f"{target_svc} -> internal_latency -> errors"
        
        # Include a snippet of actual messages for the LLM to read
        recent_messages = "\n".join(error_df['message'].unique()[:3])
        
        return {
            'service': target_svc,
            'latency': error_df['latency'].mean(),
            'error_rate': len(error_df) / 100,  # Normalized
            'similar_incidents': similar,
            'causal_chain': chain,
            'error_context': recent_messages
        }
    
    async def _action_loop(self):
        """Stage 3: Execute or simulate remediation"""
        while self._running:
            try:
                action = await asyncio.wait_for(self.action_queue.get(), timeout=1.0)
                
                if action['type'] == 'remediate':
                    logger.info(f"EXECUTING: {action['action']} on {action['target']}")
                    logger.info(f"REASON: {action['reason']}")
                    self.stats['remediations'] += 1
                    
                    # Store in history
                    self.remediation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': action['action'],
                        'target': action['target'],
                        'reason': action['reason']
                    })
                    # Keep only last 20
                    if len(self.remediation_history) > 20:
                        self.remediation_history.pop(0)
                    
                self.action_queue.task_done()
            except asyncio.TimeoutError:
                continue
    
    async def _monitoring_loop(self):
        """Stage 4: Print stats every 10s"""
        while self._running:
            await asyncio.sleep(10)
            logger.info(f"STATS: {self.stats}")

# Singleton instance for API import
controller = AsyncRCAController()

async def main():
    # Test with sample data
    await controller.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        controller.stop()
