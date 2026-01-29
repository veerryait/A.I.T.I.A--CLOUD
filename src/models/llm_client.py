import ollama
import json
import asyncio
from typing import Dict, List
from functools import lru_cache
import hashlib

class LocalDiagnostician:
    """
    Uses Phi-3 Mini (3.8B parameters, 4-bit quantized)
    Fits in M3 8GB alongside other services
    """
    def __init__(self, model: str = "phi3:mini"):
        self.model = model
        self.system_prompt = """You are an expert Site Reliability Engineer.
Analyze the system failure context and provide structured diagnosis.

Rules:
1. Identify the root cause from the causal chain provided
2. Confidence score must be 0.0-1.0
3. Action must be one of: [increase_pool, restart_service, scale_up, investigate_db, page_human]

Respond ONLY in JSON format:
{
    "root_cause": "brief technical description",
    "confidence_score": 0.95,
    "affected_service": "service_name",
    "recommended_action": "action_name",
    "reasoning": "one sentence explanation"
}"""
        
    def _generate_cache_key(self, context: Dict) -> str:
        """Cache responses for identical contexts to save GPU"""
        return hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:16]
    
    async def diagnose(self, context: Dict) -> Dict:
        """
        Async wrapper for Ollama call
        Context keys: service, latency, error_rate, similar_incidents, causal_chain
        """
        cache_key = self._generate_cache_key(context)
        
        # Build prompt
        similar = context.get('similar_incidents', [])
        similar_text = "\n".join([f"- {s['metadata']['service']}: {s['message']}" for s in similar[:3]])
        
        user_prompt = f"""Current Incident:
- Service: {context['service']}
- Latency: {context['latency']:.0f}ms
- Error Rate: {context['error_rate']:.2%}
- Causal Chain: {context.get('causal_chain', 'N/A')}
- Recent Log Context:
{context.get('error_context', 'No specific logs provided')}

Historical Similar Incidents:
{similar_text}

Provide JSON diagnosis:"""

        try:
            # Run in thread pool to not block async loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # Default executor
                lambda: ollama.chat(
                    model=self.model,
                    messages=[
                        {'role': 'system', 'content': self.system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    format='json',
                    options={
                        'temperature': 0.1,  # Deterministic
                        'num_predict': 200,  # Limit token generation for speed
                        'num_ctx': 2048      # Context window
                    }
                )
            )
            
            raw_content = response['message']['content']
            
            # Parse JSON (Phi-3 is usually good at this)
            diagnosis = json.loads(raw_content)
            
            # Validation
            if 'confidence_score' not in diagnosis:
                diagnosis['confidence_score'] = 0.5
            if 'recommended_action' not in diagnosis:
                diagnosis['recommended_action'] = 'page_human'
                
            return diagnosis
            
        except json.JSONDecodeError:
            return {
                "root_cause": "Parse error in LLM response",
                "confidence_score": 0.0,
                "recommended_action": "page_human",
                "raw_response": raw_content
            }
        except Exception as e:
            return {
                "root_cause": f"LLM Error: {str(e)}",
                "confidence_score": 0.0,
                "recommended_action": "page_human"
            }

# Test
async def test():
    client = LocalDiagnostician()
    test_context = {
        'service': 'payment-db',
        'latency': 2500,
        'error_rate': 0.45,
        'causal_chain': 'db_lock -> pool_wait -> latency',
        'similar_incidents': [
            {'metadata': {'service': 'payment-db'}, 'message': 'connection timeout'}
        ]
    }
    result = await client.diagnose(test_context)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    print("Testing LLM (first call loads model, takes 10s)...")
    asyncio.run(test())
