"""Action Interceptor interface and execution pipeline for SentreFlow."""

from abc import ABC, abstractmethod
import logging
from typing import Optional
import uuid

from app.ai.base import ModelProvider
from app.core.logging import log_security_event
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import DecisionOutcome, SecurityDecision
from app.security.policy_engine import PolicyEngine

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
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.model_provider = model_provider

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
        if self.model_provider:
            try:
                intent_analysis = await self.model_provider.analyze_intent(action, context)
            except Exception as exc:
                logger.error(f"Error during AI intent analysis: {exc}", exc_info=True)

        # Step 3: Combine into Final Security Decision
        # Policy rule BLOCK is absolute (fail-secure boundary)
        if policy_decision.decision == DecisionOutcome.BLOCK:
            final_outcome = DecisionOutcome.BLOCK
            final_risk = policy_decision.risk_score
            final_reason = policy_decision.reason
            source = "policy_engine"
        elif intent_analysis and intent_analysis.risk_score >= 80:
            final_outcome = DecisionOutcome.BLOCK
            final_risk = intent_analysis.risk_score
            final_reason = f"AI risk threshold exceeded: {intent_analysis.explanation}"
            source = f"policy+{intent_analysis.model_provider}"
        else:
            final_outcome = DecisionOutcome.ALLOW
            final_risk = max(
                policy_decision.risk_score,
                intent_analysis.risk_score if intent_analysis else 12,
            )
            final_reason = policy_decision.reason
            source = f"policy+{intent_analysis.model_provider}" if intent_analysis else "placeholder"

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
        )

        return decision
