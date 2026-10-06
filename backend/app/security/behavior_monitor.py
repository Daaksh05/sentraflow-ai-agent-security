"""Agent Behavioral Monitoring & Session Trajectory Manager for SentraFlow."""

from collections import deque
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from app.core.database import sanitize_dict
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import (
    BehaviorAnalysis,
    DecisionOutcome,
    IntentAnalysis,
    PolicyDecision,
    RiskLevel,
    TrajectoryStep,
    calculate_risk_level,
)
from app.security.trajectory import TrajectoryAnalyzer

logger = logging.getLogger("sentraflow.behavior")


class AgentSessionState:
    """Encapsulates the isolated behavioral history for a single agent session."""

    def __init__(self, session_id: str, max_window: int = 50):
        self.session_id = session_id
        self.max_window = max_window
        self.task: str = ""
        self.agent_id: str = ""
        self.steps: deque[TrajectoryStep] = deque(maxlen=max_window)
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

    def record_step(
        self,
        action: AgentAction,
        decision_outcome: str,
        risk_score: int,
        task_relevance: Optional[float] = None,
    ) -> TrajectoryStep:
        self.agent_id = action.agent_id
        self.task = action.task
        self.updated_at = datetime.now(timezone.utc)

        step = TrajectoryStep(
            step_number=len(self.steps) + 1,
            action=action.action,
            resource=action.resource,
            decision=decision_outcome,
            risk_score=risk_score,
            risk_level=calculate_risk_level(risk_score),
            task_relevance=task_relevance,
            timestamp=datetime.now(timezone.utc),
        )
        self.steps.append(step)
        return step

    def get_trajectory_steps(self) -> List[TrajectoryStep]:
        return list(self.steps)

    def reset(self) -> None:
        self.steps.clear()
        self.updated_at = datetime.now(timezone.utc)


class BehaviorMonitor:
    """Manages multi-session agent behavior tracking and orchestrates trajectory analysis."""

    def __init__(self, max_window: int = 50):
        self.max_window = max_window
        self._sessions: Dict[str, AgentSessionState] = {}

    def get_or_create_session(self, session_id: str) -> AgentSessionState:
        """Retrieves an existing session state or creates a new isolated state."""
        clean_id = (session_id or "default-session").strip()
        if clean_id not in self._sessions:
            self._sessions[clean_id] = AgentSessionState(clean_id, max_window=self.max_window)
        return self._sessions[clean_id]

    def record_and_analyze(
        self,
        action: AgentAction,
        policy_decision: Optional[PolicyDecision] = None,
        intent_analysis: Optional[IntentAnalysis] = None,
        interim_decision: Optional[DecisionOutcome] = None,
        context: Optional[ActionContext] = None,
    ) -> BehaviorAnalysis:
        """Records the intercepted action in the session history and performs trajectory analysis.
        
        Args:
            action: The requested agent action.
            policy_decision: Deterministic policy result.
            intent_analysis: NVIDIA Nemotron contextual intent analysis.
            interim_decision: Initial decision outcome before behavioral check.
            context: Action context including session identifier.
            
        Returns:
            Structured BehaviorAnalysis covering the session trajectory.
        """
        # Resolve Session ID
        effective_context = context or action.action_context
        session_id = (
            (effective_context.session_id if effective_context and effective_context.session_id else None)
            or (action.context.get("session_id") if action.context else None)
            or f"session-{action.agent_id}"
        )

        session = self.get_or_create_session(session_id)

        # Compute preliminary step risk score
        step_risk = 10
        if policy_decision:
            step_risk = max(step_risk, policy_decision.risk_score)
        if intent_analysis:
            step_risk = max(step_risk, intent_analysis.risk_score)

        outcome_str = interim_decision.value if interim_decision else (
            policy_decision.decision.value if policy_decision else "ALLOW"
        )
        task_relevance = intent_analysis.task_relevance if intent_analysis else 1.0

        # Record step in rolling session
        session.record_step(
            action=action,
            decision_outcome=outcome_str,
            risk_score=step_risk,
            task_relevance=task_relevance,
        )

        # Analyze trajectory over active session
        analysis = TrajectoryAnalyzer.analyze_sequence(
            session_id=session.session_id,
            task=action.task,
            steps=session.get_trajectory_steps(),
        )

        logger.info(
            f"Behavioral evaluation: session={session.session_id} "
            f"trajectory={analysis.trajectory_classification.value} "
            f"behavior_risk={analysis.behavior_risk_score} indicators={analysis.behavior_indicators}"
        )
        return analysis

    def get_session_trajectory(self, session_id: str) -> Optional[BehaviorAnalysis]:
        """Fetches the latest behavioral trajectory for a session."""
        if session_id not in self._sessions:
            return None
        session = self._sessions[session_id]
        return TrajectoryAnalyzer.analyze_sequence(
            session_id=session.session_id,
            task=session.task or "General Task",
            steps=session.get_trajectory_steps(),
        )

    def reset_session(self, session_id: str) -> bool:
        """Resets the history for a specific session."""
        if session_id in self._sessions:
            self._sessions[session_id].reset()
            return True
        return False

    def clear_all(self) -> None:
        """Clears all in-memory sessions (for testing)."""
        self._sessions.clear()


# Global Singleton Instance
behavior_monitor = BehaviorMonitor()
