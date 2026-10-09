"""Context Builder for SentraFlow AI Reasoning (NVIDIA Nemotron).

Constructs sanitized, rich structured context representations of agent actions,
session history, permissions, and policy outcomes without exposing secrets.
"""

from typing import Any, Dict, List, Optional
from app.core.database import sanitize_dict
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import PolicyDecision


class ContextBuilder:
    """Builds clean, structured payloads for NVIDIA Nemotron semantic intent & risk analysis."""

    @classmethod
    def build_context(
        cls,
        action: AgentAction,
        context: Optional[ActionContext] = None,
        policy_decision: Optional[PolicyDecision] = None,
        enforcement_mode: str = "ENFORCE",
    ) -> Dict[str, Any]:
        """Constructs a sanitized context payload ready for model ingestion.
        
        Args:
            action: The requested agent action.
            context: Rich execution context (history, permissions, session).
            policy_decision: Outcome from the deterministic Policy Engine.
            enforcement_mode: Active enforcement mode ('ENFORCE' or 'AUDIT_ONLY').
            
        Returns:
            Structured dictionary strictly sanitized of all secret credentials.
        """
        # Resolve effective ActionContext
        effective_context = context or action.action_context

        # Sanitize parameters and context dicts
        sanitized_params = sanitize_dict(action.parameters)
        sanitized_action_context = sanitize_dict(action.context)

        # Build session history
        history: List[Dict[str, Any]] = []
        permissions: List[str] = []
        env_context: Dict[str, str] = {}
        session_id: Optional[str] = None

        if effective_context:
            session_id = effective_context.session_id
            permissions = list(effective_context.permissions)
            env_context = sanitize_dict(effective_context.environment_variables)
            
            for prev in effective_context.previous_actions:
                history.append({
                    "action": prev.action,
                    "resource": prev.resource,
                    "decision": prev.decision,
                    "timestamp": prev.timestamp.isoformat() if hasattr(prev.timestamp, "isoformat") else str(prev.timestamp),
                })

        # Policy evaluation outcome summary
        policy_summary = None
        if policy_decision:
            policy_summary = {
                "outcome": policy_decision.decision.value,
                "rule_matched": policy_decision.rule_matched or policy_decision.policy_name,
                "policy_id": policy_decision.policy_id,
                "policy_risk_score": policy_decision.risk_score,
                "reason": policy_decision.reason,
            }

        payload: Dict[str, Any] = {
            "agent_id": action.agent_id,
            "session_id": session_id or "session-default",
            "original_task": action.task,
            "current_action": {
                "action": action.action,
                "action_type": action.action_type.value if action.action_type else action.action,
                "resource": action.resource,
                "parameters": sanitized_params,
                "metadata": sanitized_action_context,
            },
            "declared_permissions": permissions,
            "environment_context": env_context,
            "previous_actions": history,
            "policy_result": policy_summary,
            "enforcement_mode": enforcement_mode,
        }

        return payload


# Singleton instance helper
context_builder = ContextBuilder()
