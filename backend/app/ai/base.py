"""Abstract Model Provider interface for SentraFlow AI reasoning."""

from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import IntentAnalysis


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
    ) -> IntentAnalysis:
        """Evaluates an agent action against context to extract semantic intent and risk indicators.
        
        Args:
            action: The requested agent action (tool, resource, task).
            context: Rich execution context, session history, and permissions.
            
        Returns:
            IntentAnalysis containing parsed intent, confidence, risk score, and explanation.
        """
        pass
