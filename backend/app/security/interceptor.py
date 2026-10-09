"""Action Interceptor interface and execution pipeline for SentraFlow."""

from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timezone
import inspect
import logging
from typing import List, Literal, Optional
import uuid

from app.ai.base import ModelProvider
from app.core.config import settings
from app.core.database import persist_security_audit_log
from app.core.logging import log_security_event
from app.schemas.action import ActionContext, AgentAction, BatchAgentActionRequest
from app.schemas.security import (
    BatchSecurityDecisionResponse,
    BehaviorAnalysis,
    DecisionOutcome,
    EnforcementMode,
    RiskLevel,
    SecurityDecision,
    TrajectoryClassification,
    calculate_risk_level,
)
from app.security.behavior_monitor import BehaviorMonitor, behavior_monitor
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

    @abstractmethod
    async def intercept_batch(
        self,
        batch_request: BatchAgentActionRequest,
    ) -> BatchSecurityDecisionResponse:
        """Intercepts a batch of planned agent actions before execution."""
        pass


class DefaultActionInterceptor(ActionInterceptor):
    """Combines deterministic policies, adaptive response, and behavior analysis."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        model_provider: Optional[ModelProvider] = None,
        response_policy: Optional[AdaptiveResponsePolicy] = None,
        response_mode: Optional[Literal["decision", "audit_only"]] = None,
        behavior_tracker: Optional[BehaviorMonitor] = None,
        enforcement_mode: Optional[str] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.model_provider = model_provider
        self.response_policy = response_policy or AdaptiveResponsePolicy()
        self.response_mode = (
            settings.ADAPTIVE_RESPONSE_MODE if response_mode is None else response_mode
        )
        if self.response_mode not in {"decision", "audit_only"}:
            raise ValueError("response_mode must be 'decision' or 'audit_only'")
        self.behavior_tracker = behavior_tracker or behavior_monitor
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
            f"action={action.action} resource={action.resource} "
            f"mode={self.enforcement_mode}"
        )

        # Deterministic policy checks run before semantic and trajectory analysis.
        policy_decision = self.policy_engine.evaluate(action, effective_context)

        intent_analysis = None
        ai_failure = False
        if (
            self.model_provider
            and policy_decision.decision != DecisionOutcome.BLOCK
        ):
            try:
                analyze_intent = self.model_provider.analyze_intent
                parameters = inspect.signature(analyze_intent).parameters
                accepts_kwargs = any(
                    parameter.kind == inspect.Parameter.VAR_KEYWORD
                    for parameter in parameters.values()
                )
                analysis_kwargs = {
                    "action": action,
                    "context": effective_context,
                }
                if accepts_kwargs or "policy_decision" in parameters:
                    analysis_kwargs["policy_decision"] = policy_decision
                if accepts_kwargs or "enforcement_mode" in parameters:
                    analysis_kwargs["enforcement_mode"] = self.enforcement_mode
                intent_analysis = await analyze_intent(**analysis_kwargs)
            except Exception as exc:
                ai_failure = True
                logger.error(f"Error during AI intent analysis: {exc}", exc_info=True)

        # Always record the action, including policy-blocked actions, for trajectory analysis.
        behavior_analysis = self.behavior_tracker.record_and_analyze(
            action=action,
            policy_decision=policy_decision,
            intent_analysis=intent_analysis,
            interim_decision=policy_decision.decision,
            context=effective_context,
        )

        fallback_risk = (
            max(50, self.response_policy.require_approval_threshold)
            if ai_failure
            else 12
        )
        final_risk = max(
            policy_decision.risk_score,
            intent_analysis.risk_score if intent_analysis else fallback_risk,
            behavior_analysis.behavior_risk_score,
        )
        recommended_response, policy_rationale = self.response_policy.recommend(
            final_risk
        )
        if ai_failure:
            policy_rationale = (
                "AI intent analysis failed; conservative fallback risk was used. "
                + policy_rationale
            )

        is_policy_blocked = policy_decision.decision == DecisionOutcome.BLOCK
        is_ai_critical = (
            intent_analysis is not None
            and (
                intent_analysis.risk_score >= 80
                or intent_analysis.risk_level == RiskLevel.CRITICAL
                or (
                    intent_analysis.task_relevance < 0.20
                    and intent_analysis.risk_score >= 70
                )
            )
        )
        is_behavior_critical = (
            behavior_analysis.behavior_risk_score >= 80
            or behavior_analysis.behavior_risk_level == RiskLevel.CRITICAL
            or behavior_analysis.trajectory_classification
            in {
                TrajectoryClassification.DATA_EXFILTRATION,
                TrajectoryClassification.REPEATED_ATTACK,
                TrajectoryClassification.CREDENTIAL_ACCESS,
            }
        )
        is_behavior_elevated = (
            behavior_analysis.behavior_risk_score >= 50
            and (
                (intent_analysis is not None and intent_analysis.risk_score >= 50)
                or (
                    intent_analysis is not None
                    and intent_analysis.task_relevance < 0.35
                )
                or policy_decision.risk_score >= 50
            )
        )
        has_behavioral_threat = is_behavior_critical or is_behavior_elevated
        has_runtime_threat = is_ai_critical or has_behavioral_threat

        if is_policy_blocked:
            recommended_response = DecisionOutcome.BLOCK
            final_risk = max(
                policy_decision.risk_score,
                behavior_analysis.behavior_risk_score,
            )
            final_reason = policy_decision.reason
            policy_rationale = (
                "Mandatory deterministic BLOCK takes precedence over any AI or "
                "behavioral assessment. " + policy_decision.reason
            )
            source = "policy_engine"
        elif has_behavioral_threat:
            recommended_response = DecisionOutcome.BLOCK
            policy_rationale = (
                "Behavioral trajectory risk requires a BLOCK recommendation. "
                + behavior_analysis.explanation
            )
            final_reason = (
                f"Behavioral alert "
                f"({behavior_analysis.trajectory_classification.value}): "
                f"{behavior_analysis.explanation}"
            )
            source = "behavior_monitor"
        elif is_ai_critical:
            recommended_response = DecisionOutcome.BLOCK
            policy_rationale = (
                "Critical AI risk requires a BLOCK recommendation. "
                + intent_analysis.explanation
            )
            final_reason = f"Contextual AI risk detected: {intent_analysis.explanation}"
            source = f"policy+{intent_analysis.model_provider}"
        else:
            source = (
                f"policy+{intent_analysis.model_provider}+behavior"
                if intent_analysis
                else "policy+ai_fallback"
                if ai_failure
                else "policy+behavior"
            )
            if recommended_response == DecisionOutcome.ALLOW:
                final_reason = policy_decision.reason
            elif intent_analysis and intent_analysis.risk_score >= final_risk:
                final_reason = (
                    f"{recommended_response.value} recommended: "
                    f"{intent_analysis.explanation}"
                )
            else:
                final_reason = policy_rationale

        natural_outcome = (
            DecisionOutcome.BLOCK
            if is_policy_blocked
            else recommended_response
        )
        if self.response_mode == "audit_only" and not is_policy_blocked:
            # Adaptive recommendations remain telemetry; a separately enforced
            # behavioral verdict is handled below according to enforcement_mode.
            final_outcome = policy_decision.decision
            response_outcome = "recommendation_recorded_only"
        else:
            final_outcome = recommended_response
            response_outcome = (
                "mandatory_policy_block_returned"
                if is_policy_blocked
                else "decision_returned_to_caller"
            )

        if not is_policy_blocked and (
            final_outcome == DecisionOutcome.BLOCK
            or has_behavioral_threat
            or (self.response_mode == "audit_only" and has_runtime_threat)
        ):
            if self.enforcement_mode.upper() == EnforcementMode.ENFORCE.value:
                # Behavioral runtime verdicts remain independent of adaptive audit mode.
                if has_behavioral_threat:
                    final_outcome = DecisionOutcome.BLOCK
                    response_outcome = "behavioral_block_returned"
            elif self.enforcement_mode.upper() == EnforcementMode.AUDIT_ONLY.value:
                # Audit-only enforcement records all non-mandatory block signals,
                # while deterministic policy BLOCKs remain unconditional.
                final_outcome = DecisionOutcome.ALLOW
                final_reason = (
                    f"[AUDIT_ONLY MODE] Policy/Behavior violation flagged: "
                    f"{final_reason}"
                )
                source = f"{source}:audit_override"
                response_outcome = (
                    "recommendation_recorded_only"
                    if self.response_mode == "audit_only"
                    else "audit_verdict_permitted"
                )

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
            response_mode=self.response_mode,
            response_outcome=response_outcome,
            recommended_response=recommended_response,
            policy_rationale=policy_rationale,
            enforcement_mode=self.enforcement_mode,
            request_id=request_id,
            policy_decision=policy_decision,
            intent_analysis=intent_analysis,
            behavior_analysis=behavior_analysis,
        )

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
                "behavior_risk_score": behavior_analysis.behavior_risk_score,
                "trajectory_classification": (
                    behavior_analysis.trajectory_classification.value
                ),
                "behavior_indicators": behavior_analysis.behavior_indicators,
                "enforcement_mode": self.enforcement_mode,
                "natural_outcome": natural_outcome.value,
            },
            policy_rationale=decision.policy_rationale,
            response_mode=decision.response_mode,
            response_outcome=decision.response_outcome,
            recommended_response=(
                decision.recommended_response.value
                if decision.recommended_response
                else None
            ),
        )

        try:
            await persist_security_audit_log(action, decision)
        except Exception as exc:
            logger.debug(f"Audit DB persistence skipped: {exc}")

        return decision

    async def intercept_batch(
        self,
        batch_request: BatchAgentActionRequest,
    ) -> BatchSecurityDecisionResponse:
        """Evaluates planned actions and returns aggregate risk metrics."""
        decisions: List[SecurityDecision] = []
        blocked_index: Optional[int] = None
        highest_risk = 0
        allowed_count = 0
        blocked_count = 0
        last_behavior_analysis: Optional[BehaviorAnalysis] = None

        for idx, action in enumerate(batch_request.actions):
            action_context = action.action_context or batch_request.context
            decision = await self.intercept(action, action_context)
            decisions.append(decision)
            if decision.behavior_analysis:
                last_behavior_analysis = decision.behavior_analysis

            highest_risk = max(highest_risk, decision.risk_score)
            if decision.decision == DecisionOutcome.BLOCK:
                blocked_count += 1
                if blocked_index is None:
                    blocked_index = idx
                if batch_request.stop_on_first_block:
                    break
            else:
                allowed_count += 1

        overall_decision = (
            DecisionOutcome.BLOCK if blocked_count > 0 else DecisionOutcome.ALLOW
        )
        return BatchSecurityDecisionResponse(
            overall_decision=overall_decision,
            total_actions=len(decisions),
            allowed_count=allowed_count,
            blocked_count=blocked_count,
            highest_risk_score=highest_risk,
            decisions=decisions,
            blocked_action_index=blocked_index,
            behavior_analysis=last_behavior_analysis,
            enforcement_mode=self.enforcement_mode,
            evaluated_at=datetime.now(timezone.utc),
        )
