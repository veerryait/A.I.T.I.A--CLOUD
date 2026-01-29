import ollama
from groq import Groq
import json
import asyncio
import os
from typing import Dict, List
import hashlib

class LocalDiagnostician:
    """
    Hybrid Diagnostician:
    - Uses Groq (Llama 3.1 8B) if API key is present (No RAM footprint)
    - Fallbacks to Ollama (Phi-3 Mini) if running locally without key
    """
    def __init__(self, model: str = None):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            self.model = model or "llama-3.1-8b-instant"
            print(f"Using Groq Engine ({self.model})")
        else:
            self.model = model or "phi3:mini"
            print(f"Using Ollama Engine ({self.model})")
            
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

    async def diagnose(self, context: Dict) -> Dict:
        """Context keys: service, latency, error_rate, similar_incidents, causal_chain"""
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
            if self.api_key:
                # Groq API Call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                raw_content = response.choices[0].message.content
            else:
                # Local Ollama Call
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: ollama.chat(
                        model=self.model,
                        messages=[
                            {'role': 'system', 'content': self.system_prompt},
                            {'role': 'user', 'content': user_prompt}
                        ],
                        format='json',
                        options={'temperature': 0.1}
                    )
                )
                raw_content = response['message']['content']
            
            diagnosis = json.loads(raw_content)
            return diagnosis
            
        except Exception as e:
            print(f"LLM Diagnosis Error: {e}")
            return {
                "root_cause": f"Diagnosis Failed: {str(e)}",
                "confidence_score": 0.0,
                "recommended_action": "page_human",
                "reasoning": "Check LLM connectivity or API keys"
            }
