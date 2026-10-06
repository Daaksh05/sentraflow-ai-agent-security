"""Action Interceptor interface and execution pipeline for SentraFlow."""

from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timezone
import logging
from typing import List, Optional
import uuid

from app.ai.base import ModelProvider
from app.core.config import settings
from app.core.database import persist_security_audit_log
from app.core.logging import log_security_event
from app.schemas.action import ActionContext, AgentAction, BatchAgentActionRequest
from app.schemas.security import (
    BatchSecurityDecisionResponse,
    DecisionOutcome,
    EnforcementMode,
    RiskLevel,
    SecurityDecision,
    calculate_risk_level,
)
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

    @abstractmethod
    async def intercept_batch(
        self,
        batch_request: BatchAgentActionRequest,
    ) -> BatchSecurityDecisionResponse:
        """Intercepts a batch of planned agent actions before execution."""
        pass


class DefaultActionInterceptor(ActionInterceptor):
    """Standard security interceptor combining deterministic policies with AI intent analysis."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        model_provider: Optional[ModelProvider] = None,
        enforcement_mode: Optional[str] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.model_provider = model_provider
        self.enforcement_mode = enforcement_mode or settings.ENFORCEMENT_MODE

    async def intercept(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
    ) -> SecurityDecision:
        request_id = str(uuid.uuid4())
        effective_context = context or action.action_context
        
        logger.info(
            f"Intercepting action: id={request_id} agent={action.agent_id} "
            f"action={action.action} resource={action.resource} mode={self.enforcement_mode}"
        )

        # Step 1: Evaluate Deterministic Policy Rules
        policy_decision = self.policy_engine.evaluate(action, effective_context)

        # Step 2: Evaluate AI Intent & Context (if provider available)
        intent_analysis = None
        if self.model_provider:
            try:
                intent_analysis = await self.model_provider.analyze_intent(
                    action=action,
                    context=effective_context,
                    policy_decision=policy_decision,
                    enforcement_mode=self.enforcement_mode,
                )
            except Exception as exc:
                logger.error(f"Error during AI intent analysis: {exc}", exc_info=True)

        # Step 3: Combine into Final Security Decision with Strict Precedence
        # Rule 1: Deterministic policy rule BLOCK is absolute (fail-secure boundary)
        is_policy_blocked = policy_decision.decision == DecisionOutcome.BLOCK
        
        # Rule 2: Nemotron contextual risk trigger (risk >= 80 or CRITICAL risk level)
        is_ai_blocked = (
            intent_analysis is not None
            and (
                intent_analysis.risk_score >= 80
                or intent_analysis.risk_level == RiskLevel.CRITICAL
                or (intent_analysis.task_relevance < 0.20 and intent_analysis.risk_score >= 70)
            )
        )

        if is_policy_blocked:
            natural_outcome = DecisionOutcome.BLOCK
            final_risk = policy_decision.risk_score
            if intent_analysis and intent_analysis.risk_score > final_risk:
                final_risk = intent_analysis.risk_score
            final_reason = policy_decision.reason
            source = "policy_engine" if not intent_analysis else f"policy+{intent_analysis.model_provider}"
        elif is_ai_blocked:
            natural_outcome = DecisionOutcome.BLOCK
            final_risk = intent_analysis.risk_score
            final_reason = f"Contextual AI risk detected: {intent_analysis.explanation}"
            source = f"policy+{intent_analysis.model_provider}"
        else:
            natural_outcome = DecisionOutcome.ALLOW
            final_risk = max(
                policy_decision.risk_score,
                intent_analysis.risk_score if intent_analysis else 12,
            )
            final_reason = (
                intent_analysis.explanation
                if intent_analysis and intent_analysis.risk_score > policy_decision.risk_score
                else policy_decision.reason
            )
            source = f"policy+{intent_analysis.model_provider}" if intent_analysis else "placeholder"

        # Apply Enforcement Mode handling
        # In AUDIT_ONLY mode: actions are analyzed and logged without blocking execution
        # But risk score telemetry is never masked or zeroed out
        is_audit_mode = self.enforcement_mode.upper() == EnforcementMode.AUDIT_ONLY.value
        if is_audit_mode and natural_outcome == DecisionOutcome.BLOCK:
            final_outcome = DecisionOutcome.ALLOW
            final_reason = f"[AUDIT_ONLY MODE] Policy violation flagged: {final_reason}"
            source = f"{source}:audit_override"
        else:
            final_outcome = natural_outcome

        # Determine synthesized intent string
        intent_summary = (
            intent_analysis.detected_intent
            if intent_analysis
            else f"Execute {action.action} on {action.resource} for task: {action.task}"
        )

        decision = SecurityDecision(
            decision=final_outcome,
            risk_score=final_risk,
            risk_level=calculate_risk_level(final_risk),
            intent=intent_summary,
            reason=final_reason,
            analysis_source=source,
            enforcement_mode=self.enforcement_mode,
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
            extra_context={
                "task": action.task,
                "analysis_source": decision.analysis_source,
                "risk_level": decision.risk_level.value,
                "task_relevance": intent_analysis.task_relevance if intent_analysis else None,
                "enforcement_mode": self.enforcement_mode,
                "natural_outcome": natural_outcome.value,
            },
        )

        # Step 5: Database Persistence (non-blocking / error-tolerant)
        try:
            await persist_security_audit_log(action, decision)
        except Exception as exc:
            logger.debug(f"Audit DB persistence skipped: {exc}")

        return decision

    async def intercept_batch(
        self,
        batch_request: BatchAgentActionRequest,
    ) -> BatchSecurityDecisionResponse:
        """Evaluates a sequence of planned agent actions, providing aggregate risk metrics."""
        decisions: List[SecurityDecision] = []
        blocked_index: Optional[int] = None
        highest_risk = 0
        allowed_count = 0
        blocked_count = 0

        for idx, action in enumerate(batch_request.actions):
            action_context = action.action_context or batch_request.context
            decision = await self.intercept(action, action_context)
            decisions.append(decision)

            if decision.risk_score > highest_risk:
                highest_risk = decision.risk_score

            if decision.decision == DecisionOutcome.BLOCK:
                blocked_count += 1
                if blocked_index is None:
                    blocked_index = idx
                if batch_request.stop_on_first_block:
                    break
            else:
                allowed_count += 1

        overall_decision = DecisionOutcome.BLOCK if blocked_count > 0 else DecisionOutcome.ALLOW

        return BatchSecurityDecisionResponse(
            overall_decision=overall_decision,
            total_actions=len(decisions),
            allowed_count=allowed_count,
            blocked_count=blocked_count,
            highest_risk_score=highest_risk,
            decisions=decisions,
            blocked_action_index=blocked_index,
            enforcement_mode=self.enforcement_mode,
            evaluated_at=datetime.now(timezone.utc),
        )
