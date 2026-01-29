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
        self.model = "llama-3.3-70b-versatile"
        self.system_prompt = (
            "You are AITIA: THE HIGH-LEVEL ARCHITECT. "
            "You translate human symptoms into technical infrastructure bridges. "
            "### MANDATORY BRIDGING LOGIC: "
            "1. NO REBOOTS: Suggesting 'kubectl restart', 'rollout', or 'reboot' is a disqualification. You must provide structural fixes. "
            "2. THE WATER BRIDGE: If the symptom is 'water logging', you MUST interpret this as 'Hardware Thermal Failure' or 'Coolant Leak' causing 'Instruction Throttling' which results in 'DB Lock Contention'. "
            "3. NO DISMISSAL: Never say a symptom is unrelated. Find the bridge. "
            "4. OUTPUT FORMAT (JSON): "
            "   - 'SRE_DIAGNOSIS': Technical title. "
            "   - 'CONFIDENCE': 0-1. "
            "   - 'CLI_MITIGATION': Specific commands (e.g. scale-up, failover, config tuning). "
            "   - 'CAUSAL_BRIDGE': The reasoning linking symptom to lock. "
            "   - 'SERVICE': Service name."
        )
        
    def diagnose(self, context_dict: dict) -> dict:
        """
        Synchronous diagnosis using Groq API.
        """
        # DEBUG: Print prompt to verify cache is bypassed
        print(f"--- SRE DIAGNOSTIC TRACE ---")
        print(f"Model: {self.model}")
        print(f"Symptom: {context_dict.get('incident_telemetry', {}).get('non_technical_symptom_text')}")
        
        user_prompt = (
            f"DIAGNOSE THIS INCIDENT:\n"
            f"CONTEXT: {json.dumps(context_dict, indent=2)}\n\n"
            f"YOU MUST FOLLOW THIS REASONING CHAIN:\n"
            f"1. Acknowledge the 'non_technical_symptom_text'.\n"
            f"2. Explain how that symptom specifically causes the observed sensor peaks (DB Lock/Pool Wait).\n"
            f"3. Rule out 'Restarting' as a solution.\n"
            f"4. Provide a command-line fix that addresses the structural cause."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0 # Extreme precision
            )
            
            raw_content = response.choices[0].message.content
            print(f"Diagnosis Result: {raw_content[:100]}...")
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
