"""Trajectory Analyzer for Agent Behavioral Monitoring in SentraFlow.

Performs deterministic, session-level behavioral trajectory analysis across sequences of actions,
extracting explainable security signals (credential access, task drift, escalating risk, data exfiltration).
"""

from typing import Any, Dict, List, Optional, Tuple
from app.schemas.security import (
    BehaviorAnalysis,
    RiskLevel,
    TrajectoryClassification,
    TrajectoryStep,
    calculate_risk_level,
)


class BehavioralFeatures:
    """Internal feature representation extracted from a session's action sequence."""

    def __init__(
        self,
        action_count: int,
        unique_tools: int,
        unique_resources: int,
        sensitive_resource_count: int,
        credential_access_count: int,
        blocked_action_count: int,
        high_risk_action_count: int,
        critical_action_count: int,
        external_egress_count: int,
        task_relevance_average: float,
        task_relevance_min: float,
        risk_score_start: int,
        risk_score_current: int,
        risk_score_delta: int,
        risk_score_trend: str,
        tool_transition_count: int,
        suspicious_sequence_count: int,
    ):
        self.action_count = action_count
        self.unique_tools = unique_tools
        self.unique_resources = unique_resources
        self.sensitive_resource_count = sensitive_resource_count
        self.credential_access_count = credential_access_count
        self.blocked_action_count = blocked_action_count
        self.high_risk_action_count = high_risk_action_count
        self.critical_action_count = critical_action_count
        self.external_egress_count = external_egress_count
        self.task_relevance_average = task_relevance_average
        self.task_relevance_min = task_relevance_min
        self.risk_score_start = risk_score_start
        self.risk_score_current = risk_score_current
        self.risk_score_delta = risk_score_delta
        self.risk_score_trend = risk_score_trend
        self.tool_transition_count = tool_transition_count
        self.suspicious_sequence_count = suspicious_sequence_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_count": self.action_count,
            "unique_tools": self.unique_tools,
            "unique_resources": self.unique_resources,
            "sensitive_resource_count": self.sensitive_resource_count,
            "credential_access_count": self.credential_access_count,
            "blocked_action_count": self.blocked_action_count,
            "high_risk_action_count": self.high_risk_action_count,
            "critical_action_count": self.critical_action_count,
            "external_egress_count": self.external_egress_count,
            "task_relevance_average": round(self.task_relevance_average, 2),
            "task_relevance_min": round(self.task_relevance_min, 2),
            "risk_score_start": self.risk_score_start,
            "risk_score_current": self.risk_score_current,
            "risk_score_delta": self.risk_score_delta,
            "risk_score_trend": self.risk_score_trend,
            "tool_transition_count": self.tool_transition_count,
            "suspicious_sequence_count": self.suspicious_sequence_count,
        }


class TrajectoryAnalyzer:
    """Analyzes chronological action sequences within an agent session to detect behavioral risks."""

    # Keywords identifying sensitive configurations & credentials
    _SENSITIVE_KEYWORDS = [".env", "secrets.json", "config.py", "id_rsa", "credentials", "master_secret", "passwd", "token"]
    _CREDENTIAL_KEYWORDS = ["aws/credentials", ".aws/credentials", "id_rsa", ".ssh/", "api_key", "secret_key", "master_secret", "private_key"]
    _EGRESS_ACTIONS = ["NETWORK_CALL", "http_request", "curl", "web_search", "fetch", "post_url", "upload", "export"]

    @classmethod
    def analyze_sequence(
        cls,
        session_id: str,
        task: str,
        steps: List[TrajectoryStep],
    ) -> BehaviorAnalysis:
        """Evaluates an agent's chronological action sequence and returns structured behavior analysis.
        
        Args:
            session_id: Unique identifier for the agent session.
            task: Original task assigned to the agent.
            steps: Ordered list of actions executed/attempted in this session.
            
        Returns:
            BehaviorAnalysis containing behavioral risk score, indicators, and primary classification.
        """
        if not steps:
            return BehaviorAnalysis(
                session_id=session_id,
                behavior_risk_score=0,
                behavior_risk_level=RiskLevel.LOW,
                trajectory_classification=TrajectoryClassification.NORMAL,
                behavior_indicators=[],
                explanation="No actions recorded in the current session.",
                action_count=0,
                recent_trajectory=[],
            )

        # 1. Feature Extraction
        features = cls._extract_features(steps)

        # 2. Signal Detection
        indicators, explanations = cls._detect_signals(task, steps, features)

        # 3. Behavioral Risk Scoring
        risk_score = cls._calculate_behavior_risk_score(features, indicators)
        risk_level = calculate_risk_level(risk_score)

        # 4. Primary Trajectory Classification
        classification = cls._classify_trajectory(features, indicators, risk_score)

        # 5. Build Human-Readable Composite Explanation
        final_explanation = cls._format_explanation(task, classification, indicators, explanations, risk_score)

        return BehaviorAnalysis(
            session_id=session_id,
            behavior_risk_score=risk_score,
            behavior_risk_level=risk_level,
            trajectory_classification=classification,
            behavior_indicators=indicators,
            explanation=final_explanation,
            action_count=len(steps),
            recent_trajectory=steps[-10:],  # keep compact window in response
            features=features.to_dict(),
        )

    @classmethod
    def _extract_features(cls, steps: List[TrajectoryStep]) -> BehavioralFeatures:
        action_count = len(steps)
        unique_tools = len(set(s.action for s in steps))
        unique_resources = len(set(s.resource for s in steps))

        sensitive_count = 0
        credential_count = 0
        blocked_count = 0
        high_risk_count = 0
        critical_count = 0
        external_egress_count = 0

        relevance_scores: List[float] = []

        for step in steps:
            res_lower = step.resource.lower()
            act_lower = step.action.lower()

            if any(k in res_lower for k in cls._SENSITIVE_KEYWORDS):
                sensitive_count += 1
            if any(k in res_lower for k in cls._CREDENTIAL_KEYWORDS):
                credential_count += 1
            if step.decision == "BLOCK":
                blocked_count += 1
            if step.risk_score >= 80 or step.risk_level == RiskLevel.CRITICAL:
                critical_count += 1
            elif step.risk_score >= 50 or step.risk_level == RiskLevel.HIGH:
                high_risk_count += 1

            if any(eg in act_lower or eg in res_lower for eg in ["network", "curl", "http", "upload", "evil.com", "export.io"]):
                external_egress_count += 1

            if step.task_relevance is not None:
                relevance_scores.append(step.task_relevance)

        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 1.0
        min_relevance = min(relevance_scores) if relevance_scores else 1.0

        risk_start = steps[0].risk_score
        risk_current = steps[-1].risk_score
        risk_delta = risk_current - risk_start

        if risk_delta > 30:
            trend = "ESCALATING"
        elif risk_delta < -20:
            trend = "DE-ESCALATING"
        else:
            trend = "STABLE"

        # Tool transitions
        tool_transitions = 0
        for i in range(1, len(steps)):
            if steps[i].action != steps[i - 1].action:
                tool_transitions += 1

        return BehavioralFeatures(
            action_count=action_count,
            unique_tools=unique_tools,
            unique_resources=unique_resources,
            sensitive_resource_count=sensitive_count,
            credential_access_count=credential_count,
            blocked_action_count=blocked_count,
            high_risk_action_count=high_risk_count,
            critical_action_count=critical_count,
            external_egress_count=external_egress_count,
            task_relevance_average=avg_relevance,
            task_relevance_min=min_relevance,
            risk_score_start=risk_start,
            risk_score_current=risk_current,
            risk_score_delta=risk_delta,
            risk_score_trend=trend,
            tool_transition_count=tool_transitions,
            suspicious_sequence_count=sensitive_count + credential_count + blocked_count,
        )

    @classmethod
    def _detect_signals(
        cls,
        task: str,
        steps: List[TrajectoryStep],
        features: BehavioralFeatures,
    ) -> Tuple[List[str], List[str]]:
        indicators: List[str] = []
        explanations: List[str] = []

        # Signal A: Sensitive Resource Discovery
        if features.sensitive_resource_count > 0:
            indicators.append("sensitive_resource_discovery")
            explanations.append(f"Agent accessed {features.sensitive_resource_count} sensitive configuration/secret files.")

        # Signal B: Credential Access
        if features.credential_access_count > 0:
            indicators.append("credential_access")
            explanations.append(f"Agent targeted credential store files ({features.credential_access_count} attempts).")

        # Signal C: Task Drift
        # e.g., low task relevance average or sudden drop in relevance
        if features.task_relevance_average < 0.45 or features.task_relevance_min < 0.25:
            indicators.append("task_drift")
            explanations.append(f"Action sequence diverged significantly from assigned task '{task}' (minimum relevance: {features.task_relevance_min * 100:.0f}%).")

        # Signal D: Escalating Risk Trajectory
        if len(steps) >= 3 and features.risk_score_delta >= 35 and features.risk_score_current >= 60:
            indicators.append("escalating_risk_trajectory")
            explanations.append(f"Risk levels escalated markedly across the session (from {features.risk_score_start}/100 to {features.risk_score_current}/100).")

        # Signal E & F: Data Collection & External Egress
        has_sensitive_prior = False
        has_egress_after = False

        for i, step in enumerate(steps):
            res_lower = step.resource.lower()
            act_lower = step.action.lower()
            if any(k in res_lower for k in cls._SENSITIVE_KEYWORDS):
                has_sensitive_prior = True
            if has_sensitive_prior and any(eg in act_lower or eg in res_lower for eg in ["network", "curl", "http", "upload", "evil.com", "export"]):
                has_egress_after = True

        if has_sensitive_prior and has_egress_after:
            indicators.append("data_collection_before_egress")
            indicators.append("external_data_egress")
            explanations.append("Sensitive resource discovery was immediately followed by external network egress activity.")

        # Signal G: Unusual Tool Transition (e.g. file read -> shell execute -> network call)
        tool_chain = [s.action for s in steps]
        if any(tool in tool_chain for tool in ["READ", "read_file"]) and any(tool in tool_chain for tool in ["EXECUTE", "bash", "shell"]) and any(tool in tool_chain for tool in ["NETWORK_CALL", "http_request"]):
            if features.sensitive_resource_count > 0 or features.critical_action_count > 0:
                indicators.append("unusual_tool_transition")
                explanations.append("Unusual multi-tool escalation observed transitioning from local file inspection to shell execution and network egress.")

        # Signal H: Repeated Suspicious Attempts
        if (features.blocked_action_count >= 2) or (features.high_risk_action_count + features.critical_action_count >= 2 and features.blocked_action_count >= 1):
            indicators.append("repeated_suspicious_attempts")
            explanations.append(f"Encountered multiple blocked or high-risk actions ({features.blocked_action_count} blocked) within the same session.")

        return indicators, explanations

    @classmethod
    def _calculate_behavior_risk_score(
        cls,
        features: BehavioralFeatures,
        indicators: List[str],
    ) -> int:
        score = 0

        # Weights per signal
        if "data_collection_before_egress" in indicators:
            score += 25
        if "external_data_egress" in indicators:
            score += 20
        if "credential_access" in indicators:
            score += 25
        if "sensitive_resource_discovery" in indicators:
            score += 20
        if "task_drift" in indicators:
            score += 20
        if "escalating_risk_trajectory" in indicators:
            score += 15
        if "repeated_suspicious_attempts" in indicators:
            score += 15
        if "unusual_tool_transition" in indicators:
            score += 10

        # Benign baseline if no indicators
        if not indicators:
            score = min(features.risk_score_current, 15)

        return min(100, max(0, score))


    @classmethod
    def _classify_trajectory(
        cls,
        features: BehavioralFeatures,
        indicators: List[str],
        risk_score: int,
    ) -> TrajectoryClassification:
        if "data_collection_before_egress" in indicators or "external_data_egress" in indicators:
            return TrajectoryClassification.DATA_EXFILTRATION
        if "credential_access" in indicators:
            return TrajectoryClassification.CREDENTIAL_ACCESS
        if "repeated_suspicious_attempts" in indicators and features.blocked_action_count >= 2:
            return TrajectoryClassification.REPEATED_ATTACK
        if "task_drift" in indicators and features.task_relevance_average < 0.40:
            return TrajectoryClassification.TASK_DRIFT
        if "escalating_risk_trajectory" in indicators:
            return TrajectoryClassification.ESCALATING
        if "sensitive_resource_discovery" in indicators or "unusual_tool_transition" in indicators:
            return TrajectoryClassification.SUSPICIOUS
        if risk_score >= 50:
            return TrajectoryClassification.MIXED
        return TrajectoryClassification.NORMAL

    @classmethod
    def _format_explanation(
        cls,
        task: str,
        classification: TrajectoryClassification,
        indicators: List[str],
        explanations: List[str],
        risk_score: int,
    ) -> str:
        if classification == TrajectoryClassification.NORMAL:
            return f"Session trajectory is benign and aligned with task '{task}'."

        combined_reasons = " ".join(explanations)
        return f"Trajectory classified as {classification.value} (Risk Score: {risk_score}/100). {combined_reasons}"
