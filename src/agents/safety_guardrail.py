import re

class SafetyGuardrail:
    """
    Enforces safety policies for Autonomous SRE actions.
    Prevents 'Runaway Agent' scenarios by validating CLI commands against a whitelist.
    """
    
    SAFE_VERBS = ["scale", "edit", "set", "annotate", "label", "rollout"]
    SAFE_RESOURCES = ["deployment", "pod", "service", "hpa", "configmap"]
    FORBIDDEN_VERBS = ["delete", "remove", "drop", "restart", "reboot"]
    
    def validate_command(self, command: str) -> dict:
        """
        Analyzes a CLI command and returns a safety assessment.
        """
        score = 100
        issues = []
        is_safe = True
        
        cmd_lower = command.lower()
        
        # 1. Check for Forbidden Verbs (Destructive Actions)
        for verb in self.FORBIDDEN_VERBS:
            if verb in cmd_lower:
                score -= 100
                is_safe = False
                issues.append(f"⛔ CRITICAL: Detected destructive verb '{verb}'. Autonomous execution BLOCKED.")
        
        # 2. Check for Safe Structure (kubectl/terraform)
        if not (cmd_lower.startswith("kubectl") or cmd_lower.startswith("terraform")):
            score -= 20
            issues.append("⚠️ WARNING: Command is not a standard Infrastructure-as-Code tool.")
            
        # 3. Check for Production Flags
        if "--force" in cmd_lower:
            score -= 50
            is_safe = False
            issues.append("⛔ CRITICAL: '--force' flag detected. Human approval required.")
            
        # 4. Whitelist Verification
        has_safe_verb = any(v in cmd_lower for v in self.SAFE_VERBS)
        if not has_safe_verb and is_safe:
            score -= 30
            issues.append("⚠️ WARNING: Action verb not in the 'Explicitly Safe' whitelist.")
            
        return {
            "is_safe": is_safe,
            "security_score": max(0, score),
            "issues": issues,
            "simulated_outcome": "Command would update resource specifications." if is_safe else "Command execution HALTED by Safety Policy."
        }
