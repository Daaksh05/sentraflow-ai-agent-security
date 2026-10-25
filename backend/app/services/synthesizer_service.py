"""AI Policy Synthesizer Service powered by NVIDIA Nemotron 3.5 Bolt.

Transforms natural language security guidelines into strict, production-ready
zero-trust regex policy rules with dynamic hot-reload into SentraFlow.
"""

import json
import logging
import re
import uuid
import httpx
from typing import Optional

from app.core.config import settings
from app.schemas.security import DecisionOutcome
from app.schemas.synthesizer import (
    PolicySynthesizeRequest,
    PolicySynthesizeResponse,
    SynthesizedRule,
)
from app.security.policy_engine import PolicyRule
from app.services.security_service import security_service

logger = logging.getLogger("sentraflow.synthesizer")


class PolicySynthesizerService:
    """Compiles plain-English security requirements into deterministic PolicyRules."""

    def __init__(self):
        self._api_key = settings.NVIDIA_API_KEY
        self._base_url = settings.NVIDIA_BASE_URL.rstrip("/")
        self._model = settings.NVIDIA_MODEL

    def _build_system_prompt(self) -> str:
        return (
            "You are the SentraFlow Zero-Trust Policy Compiler powered by NVIDIA Nemotron.\n"
            "Your task is to convert plain-English security requirements for autonomous AI agents "
            "into a single, highly accurate deterministic regex policy rule.\n"
            "Rules must be strict, avoiding catastrophic backtracking regexes.\n"
            "Output strictly valid JSON matching this schema:\n"
            "{\n"
            '  "rule_id": "POL-SYNTH-XXXX",\n'
            '  "name": "Concise rule title",\n'
            '  "resource_pattern": "Strict regex matching the targeted resources or paths",\n'
            '  "action_pattern": "Strict regex matching action verbs (e.g. ^(READ|WRITE)$ or .* for all)",\n'
            '  "decision": "BLOCK" or "ALLOW",\n'
            '  "risk_score": Integer 0 to 100,\n'
            '  "reason": "Clear auditable reason explaining why this action is blocked or allowed",\n'
            '  "explanation": "Technical breakdown of how the regex patterns enforce the requirement"\n'
            "}"
        )

    def _synthesize_offline(self, prompt: str) -> SynthesizedRule:
        """Deterministic offline fallback synthesis for local testing without internet."""
        prompt_lower = prompt.lower()
        rule_num = str(uuid.uuid4())[:6].upper()

        if "block" in prompt_lower or "forbid" in prompt_lower or "deny" in prompt_lower or "prevent" in prompt_lower:
            decision = DecisionOutcome.BLOCK
            risk_score = 90
        else:
            decision = DecisionOutcome.ALLOW
            risk_score = 15

        # Extract target keywords
        if "tmp" in prompt_lower and "py" in prompt_lower:
            resource_pattern = r"^/tmp/.*\.py$"
            action_pattern = r"^(EXECUTE|RUN|BASH|SHELL)$"
            name = "Block /tmp Python Execution"
            reason = "Execution of scripts in /tmp is blocked to prevent untrusted code execution."
        elif "etc" in prompt_lower:
            resource_pattern = r"^/etc/.*"
            action_pattern = r"^(WRITE|DELETE|EXECUTE)$"
            name = "Protect /etc System Directory"
            reason = "Direct writes or execution in /etc are strictly blocked by security policy."
        elif "database" in prompt_lower or "db" in prompt_lower:
            resource_pattern = r"(prod_db|production|customer_pii|drop table)"
            action_pattern = r"(DROP|DELETE|UPDATE|TRUNCATE)"
            name = "Database Mutation Guard"
            reason = "Destructive database operations and production database writes are prohibited."
        elif "network" in prompt_lower or "curl" in prompt_lower or "egress" in prompt_lower:
            resource_pattern = r"(http://|https://|ftp://|curl|wget)"
            action_pattern = r"(NETWORK_CALL|POST|UPLOAD|EXECUTE)"
            name = "External Egress Quarantine"
            reason = "Unapproved external network calls and data egress operations are blocked."
        else:
            resource_pattern = r".*"
            action_pattern = r"(DELETE|EXECUTE)"
            name = f"Custom Zero-Trust Boundary ({rule_num})"
            reason = f"Enforced according to administrator policy prompt: '{prompt}'."

        return SynthesizedRule(
            rule_id=f"POL-SYNTH-{rule_num}",
            name=name,
            resource_pattern=resource_pattern,
            action_pattern=action_pattern,
            decision=decision,
            risk_score=risk_score,
            reason=reason,
            explanation="Synthesized using SentraFlow heuristic rule compiler (offline fallback mode).",
        )

    async def synthesize(self, request: PolicySynthesizeRequest) -> PolicySynthesizeResponse:
        """Translates natural language prompt into an active deterministic policy rule."""
        synthesized_rule: Optional[SynthesizedRule] = None

        if self._api_key and not self._api_key.startswith("your_"):
            try:
                headers = {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }
                body = {
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": self._build_system_prompt()},
                        {"role": "user", "content": f"Synthesize a security rule for: {request.prompt}"},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                }

                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers=headers,
                        json=body,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)

                    # Validate DecisionOutcome
                    raw_dec = str(parsed.get("decision", "BLOCK")).upper()
                    decision = DecisionOutcome.ALLOW if "ALLOW" in raw_dec else DecisionOutcome.BLOCK

                    synthesized_rule = SynthesizedRule(
                        rule_id=parsed.get("rule_id", f"POL-SYNTH-{uuid.uuid4().hex[:6].upper()}"),
                        name=parsed.get("name", "Synthesized Policy Rule"),
                        resource_pattern=parsed.get("resource_pattern", ".*"),
                        action_pattern=parsed.get("action_pattern", ".*"),
                        decision=decision,
                        risk_score=int(parsed.get("risk_score", 85)),
                        reason=parsed.get("reason", "Synthesized by NVIDIA Nemotron"),
                        explanation=parsed.get("explanation", "Compiled from natural language specification."),
                    )
            except Exception as exc:
                logger.warning(f"Live Nemotron synthesis failed ({exc}); using offline compiler.")
                synthesized_rule = self._synthesize_offline(request.prompt)
        else:
            synthesized_rule = self._synthesize_offline(request.prompt)

        # Validate that compiled regexes are strictly valid in Python re
        try:
            re.compile(synthesized_rule.resource_pattern)
            re.compile(synthesized_rule.action_pattern)
            validation_status = "VALID_REGEX"
        except re.error as err:
            logger.error(f"Synthesized invalid regex: {err}")
            synthesized_rule.resource_pattern = re.escape(synthesized_rule.resource_pattern)
            validation_status = "ESCAPED_FALLBACK"

        # Hot-reload into active engine if requested
        activated = False
        if request.auto_activate:
            new_rule = PolicyRule(
                rule_id=synthesized_rule.rule_id,
                name=synthesized_rule.name,
                resource_pattern=synthesized_rule.resource_pattern,
                action_pattern=synthesized_rule.action_pattern,
                outcome=synthesized_rule.decision,
                risk_score=synthesized_rule.risk_score,
                reason=synthesized_rule.reason,
            )
            security_service.policy_engine.add_custom_rule(new_rule, prioritize=True)
            activated = True

        return PolicySynthesizeResponse(
            success=True,
            prompt=request.prompt,
            rule=synthesized_rule,
            activated=activated,
            total_active_rules=len(security_service.policy_engine.rules),
            model_name=self._model,
            validation_status=validation_status,
        )


policy_synthesizer = PolicySynthesizerService()
