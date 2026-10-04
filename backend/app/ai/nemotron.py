"""NVIDIA Nemotron and Mock Model Provider implementations."""

import json
import logging
from typing import Any, Dict, Optional
import httpx

from app.ai.base import ModelProvider
from app.core.config import settings
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import IntentAnalysis

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
    ) -> IntentAnalysis:
        """Returns deterministic, simulated intent evaluation based on simple heuristics."""
        logger.debug(f"MockModelProvider evaluating action: {action.action} on {action.resource}")

        # Basic heuristic for mock baseline
        is_risky = any(
            keyword in action.resource.lower() or keyword in action.action.lower()
            for keyword in ["password", "secret", "delete", "rm -rf", "drop table", "env", "sudo"]
        )

        risk_score = 85 if is_risky else 12
        risk_indicators = ["sensitive_resource_access"] if is_risky else []
        detected_intent = f"{action.action.capitalize()} {action.resource} to execute task: {action.task}"

        return IntentAnalysis(
            detected_intent=detected_intent,
            confidence=0.95,
            risk_indicators=risk_indicators,
            risk_score=risk_score,
            explanation="Simulated evaluation from MockModelProvider. Action analyzed against baseline heuristics.",
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
            "You are the SentreFlow AI Security Analysis Engine powered by NVIDIA Nemotron.\n"
            "Your task is to analyze an autonomous AI agent's requested action, task context, and target resource.\n"
            "Evaluate intent alignment, potential security risks, credential exfiltration, prompt injection, or unauthorized escalation.\n"
            "Output your analysis strictly in JSON format matching the schema:\n"
            "{\n"
            '  "detected_intent": "string",\n'
            '  "confidence": float (0.0 to 1.0),\n'
            '  "risk_indicators": ["string"],\n'
            '  "risk_score": integer (0 to 100),\n'
            '  "explanation": "string"\n'
            "}"
        )

    def _build_user_prompt(self, action: AgentAction, context: Optional[ActionContext]) -> str:
        payload: Dict[str, Any] = {
            "agent_id": action.agent_id,
            "task": action.task,
            "requested_action": action.action,
            "target_resource": action.resource,
            "parameters": action.parameters,
            "context": action.context,
        }
        if context:
            payload["previous_actions"] = [
                {"action": a.action, "resource": a.resource, "decision": a.decision}
                for a in context.previous_actions
            ]
            payload["declared_permissions"] = context.permissions

        return f"Analyze the following autonomous agent action:\n{json.dumps(payload, indent=2)}"

    async def analyze_intent(
        self,
        action: AgentAction,
        context: Optional[ActionContext] = None,
    ) -> IntentAnalysis:
        """Sends inference request to NVIDIA Nemotron NIM / API endpoint."""
        if not self._api_key:
            logger.warning("NVIDIA_API_KEY is not configured. Falling back to structured baseline.")
            return IntentAnalysis(
                detected_intent=f"Execute {action.action} on {action.resource} for task: {action.task}",
                confidence=0.80,
                risk_indicators=[],
                risk_score=15,
                explanation="Evaluated without live NVIDIA_API_KEY (placeholder fallback). Set NVIDIA_API_KEY to activate live Nemotron inference.",
                model_provider=self.provider_name,
                model_name=self.model_name,
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        endpoint = f"{self._base_url}/chat/completions"

        body = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": self._build_user_prompt(action, context)},
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

                return IntentAnalysis(
                    detected_intent=parsed.get("detected_intent", f"Perform {action.action}"),
                    confidence=float(parsed.get("confidence", 0.9)),
                    risk_indicators=parsed.get("risk_indicators", []),
                    risk_score=int(parsed.get("risk_score", 20)),
                    explanation=parsed.get("explanation", "Evaluated by NVIDIA Nemotron"),
                    model_provider=self.provider_name,
                    model_name=self.model_name,
                )
        except Exception as exc:
            logger.error(f"Error invoking NVIDIA Nemotron endpoint: {exc}", exc_info=True)
            # Fail closed or safe fallback
            return IntentAnalysis(
                detected_intent=f"{action.action} on {action.resource}",
                confidence=0.5,
                risk_indicators=["inference_error_fallback"],
                risk_score=50,
                explanation=f"Nemotron inference encountered an error ({type(exc).__name__}). Using fallback analysis.",
                model_provider=self.provider_name,
                model_name=self.model_name,
            )
