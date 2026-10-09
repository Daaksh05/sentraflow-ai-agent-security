"""Action Interceptor interface and execution pipeline for SentraFlow."""

from abc import ABC, abstractmethod
import logging
from typing import Literal, Optional
import uuid

from app.ai.base import ModelProvider
from app.core.config import settings
from app.core.logging import log_security_event
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import DecisionOutcome, SecurityDecision
from app.security.policy_engine import PolicyEngine
from app.security.response_policy import AdaptiveResponsePolicy

logger = logging.getLogger("sentraflow.interceptor")


class ActionInterceptor(ABC):
    """Abstract interface defining the interception hook for agent actions."""

    @abstractmethod
    async def intercept(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
    ) -> SecurityDecision:
        """Intercepts an action requested by an AI agent before execution."""
        pass


class DefaultActionInterceptor(ActionInterceptor):
    """Standard security interceptor combining deterministic policies with AI intent analysis."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        model_provider: Optional[ModelProvider] = None,
        response_policy: Optional[AdaptiveResponsePolicy] = None,
        response_mode: Optional[Literal["decision", "audit_only"]] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.model_provider = model_provider
        self.response_policy = response_policy or AdaptiveResponsePolicy()
        self.response_mode = (
            settings.ADAPTIVE_RESPONSE_MODE if response_mode is None else response_mode
        )
        if self.response_mode not in {"decision", "audit_only"}:
            raise ValueError("response_mode must be 'decision' or 'audit_only'")

    async def intercept(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
    ) -> SecurityDecision:
        request_id = str(uuid.uuid4())
        logger.info(f"Intercepting action: id={request_id} agent={action.agent_id} action={action.action} resource={action.resource}")

        # Step 1: Evaluate Deterministic Policy Rules
        policy_decision = self.policy_engine.evaluate(action, context)

        # Step 2: Evaluate AI Intent & Context (if provider available)
        intent_analysis = None
        ai_failure = False
        if (
            self.model_provider
            and policy_decision.decision != DecisionOutcome.BLOCK
        ):
            try:
                intent_analysis = await self.model_provider.analyze_intent(action, context)
            except Exception as exc:
                ai_failure = True
                logger.error(f"Error during AI intent analysis: {exc}", exc_info=True)

        # Step 3: Derive the risk-based recommendation; deterministic BLOCK remains absolute.
        fallback_risk = (
            max(50, self.response_policy.require_approval_threshold)
            if ai_failure
            else 12
        )
        final_risk = max(
            policy_decision.risk_score,
            intent_analysis.risk_score if intent_analysis else fallback_risk,
        )
        recommended_response, policy_rationale = self.response_policy.recommend(final_risk)
        if ai_failure:
            policy_rationale = (
                "AI intent analysis failed; conservative fallback risk was used. "
                + policy_rationale
            )

        if policy_decision.decision == DecisionOutcome.BLOCK:
            recommended_response = DecisionOutcome.BLOCK
            final_risk = policy_decision.risk_score
            final_reason = policy_decision.reason
            policy_rationale = (
                "Mandatory deterministic BLOCK takes precedence over any AI assessment. "
                + policy_decision.reason
            )
            source = "policy_engine"
        else:
            source = (
                f"policy+{intent_analysis.model_provider}"
                if intent_analysis
                else "policy+ai_fallback" if ai_failure else "placeholder"
            )
            if recommended_response == DecisionOutcome.ALLOW:
                final_reason = policy_decision.reason
            elif intent_analysis:
                final_reason = (
                    f"{recommended_response.value} recommended: "
                    f"{intent_analysis.explanation}"
                )
            else:
                final_reason = policy_rationale

        if self.response_mode == "audit_only" and policy_decision.decision != DecisionOutcome.BLOCK:
            final_outcome = policy_decision.decision
            response_outcome = "recommendation_recorded_only"
        else:
            final_outcome = recommended_response
            response_outcome = (
                "mandatory_policy_block_returned"
                if policy_decision.decision == DecisionOutcome.BLOCK
                else "decision_returned_to_caller"
            )
        # Determine synthesized intent string
        intent_summary = (
            intent_analysis.detected_intent
            if intent_analysis
            else f"Execute {action.action} on {action.resource} for task: {action.task}"
        )

        decision = SecurityDecision(
            decision=final_outcome,
            risk_score=final_risk,
            intent=intent_summary,
            reason=final_reason,
            analysis_source=source,
            request_id=request_id,
            policy_decision=policy_decision,
            intent_analysis=intent_analysis,
            response_mode=self.response_mode,
            response_outcome=response_outcome,
            recommended_response=recommended_response,
            policy_rationale=policy_rationale,
        )

        # Step 4: Traceable Security Audit Log
        log_security_event(
            agent_id=action.agent_id,
            action=action.action,
            resource=action.resource,
            decision=decision.decision.value,
            risk_score=decision.risk_score,
            reason=decision.reason,
            request_id=request_id,
            extra_context={"task": action.task, "analysis_source": decision.analysis_source},
            policy_rationale=decision.policy_rationale,
            response_mode=decision.response_mode,
            response_outcome=decision.response_outcome,
            recommended_response=(
                decision.recommended_response.value
                if decision.recommended_response
                else None
            ),
        )

        return decision
