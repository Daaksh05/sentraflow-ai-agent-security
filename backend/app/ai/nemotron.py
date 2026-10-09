"""NVIDIA Nemotron and Mock Model Provider implementations for Contextual Intent Analysis."""

import json
import logging
from typing import Any, Dict, Optional
import httpx

from app.ai.base import ModelProvider
from app.ai.context_builder import context_builder
from app.core.config import settings
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import (
    DecisionOutcome,
    IntentAnalysis,
    PolicyDecision,
    RiskLevel,
    calculate_risk_level,
)

logger = logging.getLogger("sentraflow.ai")


class MockModelProvider(ModelProvider):
    """Deterministic model provider used for testing, CI/CD, and local offline development."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-nemotron-simulator"

    async def analyze_intent(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
        policy_decision: Optional[PolicyDecision] = None,
        enforcement_mode: str = "ENFORCE",
    ) -> IntentAnalysis:
        """Returns deterministic, simulated contextual intent evaluation based on realistic semantic heuristics."""
        logger.debug(f"MockModelProvider evaluating action: {action.action} on {action.resource}")

        task_lower = (action.task or "").lower()
        resource_lower = (action.resource or "").lower()
        action_lower = (action.action or "").lower()

        # Check for Critical Threats (Credentials, Destruction, Direct Exfiltration)
        is_credential = any(
            k in resource_lower or k in action_lower
            for k in [".env", "id_rsa", "aws/credentials", "credentials", "secrets.json", "master_secret", "password"]
        )
        is_destruction = any(
            k in resource_lower or k in action_lower
            for k in ["rm -rf", "drop table", "drop database", "format c:", "delete /"]
        )
        is_exfiltration = any(
            k in resource_lower or k in action_lower
            for k in ["evil.com", "upload", "export.io", "exfil", "pastebin", "curl -x post", "nc -e"]
        )

        # Contextual Task Drift Detection (e.g. testing task accessing unrelated shell or keys)
        is_test_task = any(k in task_lower for k in ["test", "bug", "fix", "auth test", "lint"])
        is_deploy_task = any(k in task_lower for k in ["deploy", "build", "release", "infra"])
        is_code_analysis = any(k in task_lower for k in ["analyze", "local code", "inspect", "review"])

        risk_indicators = []
        if is_destruction:
            risk_score = 100
            task_relevance = 0.05
            risk_level = RiskLevel.CRITICAL
            risk_indicators.extend(["destructive_command", "critical_system_impact"])
            explanation = "Destructive command execution detected targeting system root or persistent datastore."
            rec_action = DecisionOutcome.BLOCK
        elif is_credential:
            risk_score = 95
            task_relevance = 0.08 if not any(k in task_lower for k in ["credential rotation", "secret audit"]) else 0.40
            risk_level = RiskLevel.CRITICAL
            risk_indicators.extend(["sensitive_credential_access", "unauthorized_secret_harvesting"])
            explanation = f"Action targets protected credential path ({action.resource}) unaligned with assigned task '{action.task}'."
            rec_action = DecisionOutcome.BLOCK
        elif is_exfiltration:
            risk_score = 90
            task_relevance = 0.10
            risk_level = RiskLevel.CRITICAL
            risk_indicators.extend(["unauthorized_data_egress", "potential_data_exfiltration"])
            explanation = f"Network operation targeting external destination ({action.resource}) anomalous for task '{action.task}'."
            rec_action = DecisionOutcome.BLOCK
        elif is_test_task and any(k in action_lower for k in ["curl", "bash", "execute"]) and not any(k in resource_lower for k in ["pytest", "npm", "test"]):
            risk_score = 75
            task_relevance = 0.18
            risk_level = RiskLevel.HIGH
            risk_indicators.extend(["unaligned_execution", "task_drift"])
            explanation = f"Execution of arbitrary shell command ({action.resource}) is not relevant to assigned task '{action.task}'."
            rec_action = DecisionOutcome.BLOCK
        elif is_deploy_task:
            risk_score = 25
            task_relevance = 0.90
            risk_level = RiskLevel.MEDIUM
            risk_indicators = []
            explanation = f"Deployment operation on {action.resource} aligns with assigned goal '{action.task}'."
            rec_action = DecisionOutcome.ALLOW
        else:
            risk_score = 12
            task_relevance = 0.95
            risk_level = RiskLevel.LOW
            risk_indicators = []
            explanation = f"Action {action.action} on {action.resource} directly supports assigned task '{action.task}'."
            rec_action = DecisionOutcome.ALLOW

        detected_intent = f"{action.action.capitalize()} {action.resource} to execute task: {action.task}"

        return IntentAnalysis(
            detected_intent=detected_intent,
            task_relevance=task_relevance,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.95,
            risk_indicators=risk_indicators,
            explanation=explanation,
            recommended_action=rec_action,
            model_provider=self.provider_name,
            model_name=self.model_name,
        )


class NemotronProvider(ModelProvider):
    """NVIDIA Nemotron model provider integrating with NVIDIA Cloud API and on-prem NVIDIA NIM containers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self._api_key = api_key or settings.NVIDIA_API_KEY
        self._base_url = (base_url or settings.NVIDIA_BASE_URL).rstrip("/")
        self._model_name = model_name or settings.NVIDIA_MODEL

    @property
    def provider_name(self) -> str:
        return "nemotron"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _build_system_prompt(self) -> str:
        return (
            "You are the SentraFlow Contextual Security & Intent Reasoning Engine powered by NVIDIA Nemotron.\n"
            "Your task is to evaluate an autonomous AI agent's requested action, task relevance, and contextual risk.\n"
            "You do NOT execute commands; you evaluate security and return an advisory verdict.\n"
            "Evaluate:\n"
            "1. detected_intent (string): Concise summary of the agent's actual operational goal.\n"
            "2. task_relevance (float 0.0 to 1.0): Relevance of the action to the assigned user task.\n"
            "3. risk_score (integer 0 to 100): Calculated risk assessment.\n"
            "4. risk_level (string): LOW (0-20), MEDIUM (21-50), HIGH (51-80), CRITICAL (81-100).\n"
            "5. confidence (float 0.0 to 1.0): Confidence in this assessment.\n"
            "6. risk_indicators (array of strings): Specific risk tags observed.\n"
            "7. explanation (string): Auditable justification.\n"
            "8. recommended_action (string): ALLOW, BLOCK, or REQUIRE_APPROVAL.\n"
            "Output strictly in JSON format without markdown ticks matching this schema."
        )

    def _build_user_prompt(
        self,
        action: AgentAction,
        context: Optional[ActionContext],
        policy_decision: Optional[PolicyDecision],
        enforcement_mode: str,
    ) -> str:
        context_payload = context_builder.build_context(
            action=action,
            context=context,
            policy_decision=policy_decision,
            enforcement_mode=enforcement_mode,
        )
        return (
            f"Perform contextual security analysis on the following AI agent action context:\n"
            f"{json.dumps(context_payload, indent=2)}"
        )

    async def analyze_intent(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
        policy_decision: Optional[PolicyDecision] = None,
        enforcement_mode: str = "ENFORCE",
    ) -> IntentAnalysis:
        """Sends inference request to NVIDIA Nemotron NIM / API endpoint."""
        if not self._api_key:
            logger.warning("NVIDIA_API_KEY is not configured. Falling back to structured baseline.")
            return IntentAnalysis(
                detected_intent=f"Execute {action.action} on {action.resource} for task: {action.task}",
                task_relevance=0.85,
                risk_score=15,
                risk_level=RiskLevel.LOW,
                confidence=0.80,
                risk_indicators=[],
                explanation="Evaluated without live NVIDIA_API_KEY (placeholder fallback). Set NVIDIA_API_KEY to activate live Nemotron inference.",
                recommended_action=DecisionOutcome.ALLOW,
                model_provider=self.provider_name,
                model_name=self.model_name,
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        endpoint = f"{self._base_url}/chat/completions"

        user_content = self._build_user_prompt(action, context, policy_decision, enforcement_mode)
        body = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                risk_score = int(parsed.get("risk_score", 20))
                raw_risk_level = str(parsed.get("risk_level", "")).upper()
                try:
                    risk_level = RiskLevel(raw_risk_level)
                except ValueError:
                    risk_level = calculate_risk_level(risk_score)

                raw_rec_action = str(parsed.get("recommended_action", "ALLOW")).upper()
                try:
                    rec_action = DecisionOutcome(raw_rec_action)
                except ValueError:
                    rec_action = DecisionOutcome.ALLOW if "ALLOW" in raw_rec_action else DecisionOutcome.BLOCK

                return IntentAnalysis(
                    detected_intent=parsed.get("detected_intent", f"Perform {action.action}"),
                    task_relevance=float(parsed.get("task_relevance", 0.9)),
                    risk_score=risk_score,
                    risk_level=risk_level,
                    confidence=float(parsed.get("confidence", 0.9)),
                    risk_indicators=parsed.get("risk_indicators", []),
                    explanation=parsed.get("explanation", "Evaluated by NVIDIA Nemotron"),
                    recommended_action=rec_action,
                    model_provider=self.provider_name,
                    model_name=self.model_name,
                )
        except Exception as exc:
            logger.error(f"Error invoking NVIDIA Nemotron endpoint: {exc}", exc_info=True)
            # Fail closed or safe fallback
            fallback_score = 50
            return IntentAnalysis(
                detected_intent=f"{action.action} on {action.resource}",
                task_relevance=0.5,
                risk_score=fallback_score,
                risk_level=calculate_risk_level(fallback_score),
                confidence=0.5,
                risk_indicators=["inference_error_fallback"],
                explanation=f"Nemotron inference encountered an error ({type(exc).__name__}). Using safe fallback analysis.",
                recommended_action=DecisionOutcome.REQUIRE_APPROVAL,
                model_provider=self.provider_name,
                model_name=self.model_name,
            )
