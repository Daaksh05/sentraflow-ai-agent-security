"""Security service layer orchestrating policy, AI evaluation, and batch execution."""

from typing import Optional
from app.ai import get_model_provider
from app.core.config import settings
from app.schemas.action import ActionContext, AgentAction, BatchAgentActionRequest
from app.schemas.security import BatchSecurityDecisionResponse, SecurityDecision
from app.security.interceptor import DefaultActionInterceptor
from app.security.policy_engine import PolicyEngine


class SecurityService:
    """Service handling action evaluation, policy checks, intent analysis, and batch processing."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        interceptor: Optional[DefaultActionInterceptor] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        
        # Load configured policy profile if specified and non-default
        if settings.ACTIVE_POLICY_PROFILE and settings.ACTIVE_POLICY_PROFILE not in ["default_builtin", "default"]:
            try:
                self.policy_engine.switch_profile(settings.ACTIVE_POLICY_PROFILE)
            except Exception:
                pass

        model_provider = get_model_provider()
        self.interceptor = interceptor or DefaultActionInterceptor(
            policy_engine=self.policy_engine,
            model_provider=model_provider,
            enforcement_mode=settings.ENFORCEMENT_MODE,
        )

    async def evaluate_action(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
    ) -> SecurityDecision:
        """Evaluates a single agent action through the configured interceptor pipeline."""
        effective_context = context or action.action_context
        return await self.interceptor.intercept(action, effective_context)

    async def evaluate_batch(
        self,
        batch_request: BatchAgentActionRequest,
    ) -> BatchSecurityDecisionResponse:
        """Evaluates a batch sequence of agent actions."""
        return await self.interceptor.intercept_batch(batch_request)

    def set_enforcement_mode(self, mode: str) -> None:
        """Dynamically updates interceptor enforcement mode ('ENFORCE' or 'AUDIT_ONLY')."""
        self.interceptor.enforcement_mode = mode

    def switch_policy_profile(self, profile_identifier: str) -> int:
        """Switches the active deterministic policy profile."""
        return self.policy_engine.switch_profile(profile_identifier)


# Default singleton instance
security_service = SecurityService()
