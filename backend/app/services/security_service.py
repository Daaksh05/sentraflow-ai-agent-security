"""Security service layer orchestrating policy and AI evaluation."""

from typing import Optional
from app.ai import get_model_provider
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import SecurityDecision
from app.security.interceptor import DefaultActionInterceptor
from app.security.policy_engine import PolicyEngine


class SecurityService:
    """Service handling action evaluation, policy checks, and intent analysis."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        interceptor: Optional[DefaultActionInterceptor] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        model_provider = get_model_provider()
        self.interceptor = interceptor or DefaultActionInterceptor(
            policy_engine=self.policy_engine,
            model_provider=model_provider,
        )

    async def evaluate_action(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
    ) -> SecurityDecision:
        """Evaluates an agent action through the configured interceptor pipeline."""
        return await self.interceptor.intercept(action, context)


# Default singleton instance
security_service = SecurityService()
