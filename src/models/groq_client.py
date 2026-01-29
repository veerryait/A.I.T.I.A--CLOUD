from groq import Groq
import json
import logging

logger = logging.getLogger("GroqDiagnostician")

class GroqDiagnostician:
    """
    Groq-specific diagnostician for cloud deployment (no local dependencies).
    Uses Llama 3.1 8B for high-speed SRE analysis.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Groq API Key is required for cloud deployment.")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
        self.system_prompt = (
            "You are AITIA SRE AI. Analyze root cause. "
            "JSON response only with keys: root_cause, confidence_score (0-1), "
            "recommended_action, affected_service, reasoning"
        )
        
    def diagnose(self, context_dict: dict) -> dict:
        """
        Synchronous diagnosis using Groq API.
        Handles rate limits (429) by returning a low-confidence response.
        """
        # Format the prompt with context
        user_prompt = f"Context: {json.dumps(context_dict, indent=2)}"
        
        try:
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
            return json.loads(raw_content)
            
        except Exception as e:
            # Handle rate limits or other API errors
            err_str = str(e)
            if "429" in err_str:
                logger.warning("Groq Rate Limit hit (429). Returning low confidence.")
                return {
                    "root_cause": "Diagnosis throttled by rate limit",
                    "confidence_score": 0.1,
                    "recommended_action": "page_human",
                    "affected_service": context_dict.get("service", "unknown"),
                    "reasoning": "Groq API returned 429 (Rate Limit). Try again after cooldown."
                }
            
            logger.error(f"Groq API Error: {err_str}")
            return {
                "root_cause": f"Diagnosis failed: {err_str}",
                "confidence_score": 0.0,
                "recommended_action": "page_human",
                "affected_service": context_dict.get("service", "unknown"),
                "reasoning": "Communication error with Groq Cloud API."
            }
