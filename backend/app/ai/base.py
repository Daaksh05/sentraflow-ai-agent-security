"""Abstract Model Provider interface for SentraFlow AI reasoning."""

from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import IntentAnalysis, PolicyDecision


class ModelProvider(ABC):
    """Abstract interface decoupling the security layer from specific LLM providers.
    
    This ensures that NVIDIA Nemotron, NIM self-hosted endpoints, or alternate models
    can be used or swapped without rewriting the security engine or policy interceptors.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider implementation."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the active model."""
        pass

    @abstractmethod
    async def analyze_intent(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
        policy_decision: Optional[PolicyDecision] = None,
        enforcement_mode: str = "ENFORCE",
    ) -> IntentAnalysis:
        """Evaluates an agent action against context to extract semantic intent, task relevance, and risk indicators.
        
        Args:
            action: The requested agent action (tool, resource, task).
            context: Rich execution context, session history, and permissions.
            policy_decision: Outcome from the deterministic policy engine.
            enforcement_mode: Active enforcement mode ('ENFORCE' or 'AUDIT_ONLY').
            
        Returns:
            IntentAnalysis containing parsed intent, task relevance, risk score, risk level, confidence, and explanation.
        """
        pass
