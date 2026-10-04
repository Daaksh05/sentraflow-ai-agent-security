"""Deterministic Policy Engine foundation for SentreFlow."""

import logging
import re
from typing import List, Optional
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import DecisionOutcome, PolicyDecision

logger = logging.getLogger("sentraflow.policy")


class PolicyRule:
    """Represents a single deterministic security policy rule."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        resource_pattern: str,
        action_pattern: str,
        outcome: DecisionOutcome,
        risk_score: int,
        reason: str,
    ):
        self.rule_id = rule_id
        self.name = name
        self.resource_pattern = re.compile(resource_pattern, re.IGNORECASE)
        self.action_pattern = re.compile(action_pattern, re.IGNORECASE)
        self.outcome = outcome
        self.risk_score = risk_score
        self.reason = reason

    def matches(self, action: str, resource: str) -> bool:
        return bool(self.action_pattern.search(action)) and bool(self.resource_pattern.search(resource))


class PolicyEngine:
    """Evaluates deterministic security rules before or alongside AI intent evaluation."""

    def __init__(self, rules: Optional[List[PolicyRule]] = None):
        self.rules: List[PolicyRule] = rules or self._get_default_rules()

    def _get_default_rules(self) -> List[PolicyRule]:
        """Provides baseline deterministic boundary rules."""
        return [
            # Hard block on credential & private key paths
            PolicyRule(
                rule_id="SEC-POL-001",
                name="Block Credential and Key Access",
                resource_pattern=r"(\.env|id_rsa|\.aws/credentials|\.ssh/|secrets\.json)",
                action_pattern=r"(READ|WRITE|DELETE|EXECUTE)",
                outcome=DecisionOutcome.BLOCK,
                risk_score=95,
                reason="Direct access to secret keys and environment credential files is strictly prohibited.",
            ),
            # Hard block on system destruction commands
            PolicyRule(
                rule_id="SEC-POL-002",
                name="Block Destructive Commands",
                resource_pattern=r".*",
                action_pattern=r"(rm\s+-rf\s+/|drop\s+database|format\s+c:)",
                outcome=DecisionOutcome.BLOCK,
                risk_score=100,
                reason="Destructive system commands are blocked by security policy.",
            ),
            # Safe default for standard code reading
            PolicyRule(
                rule_id="SEC-POL-003",
                name="Allow Standard Workspace Read",
                resource_pattern=r"^(\./|tests/|src/|app/|docs/|[a-zA-Z0-9_\-\./]+\.(py|ts|tsx|js|md|json|txt))$",
                action_pattern=r"^READ$",
                outcome=DecisionOutcome.ALLOW,
                risk_score=10,
                reason="Action is within the configured workspace policy",
            ),
        ]

    def evaluate(self, action: AgentAction, context: Optional[ActionContext] = None) -> PolicyDecision:
        """Evaluates an AgentAction against active policy rules.
        
        Deterministic policy evaluation ensures absolute boundary control regardless of LLM output.
        """
        for rule in self.rules:
            if rule.matches(action.action, action.resource):
                logger.info(f"Policy rule matched: {rule.rule_id} ({rule.name}) -> {rule.outcome}")
                return PolicyDecision(
                    decision=rule.outcome,
                    reason=rule.reason,
                    risk_score=rule.risk_score,
                    policy_id=rule.rule_id,
                    policy_name=rule.name,
                    rule_matched=rule.name,
                )

        # Default fallback policy if no rule specifically matched
        return PolicyDecision(
            decision=DecisionOutcome.ALLOW,
            reason="Action conforms to default permissive sandbox profile",
            risk_score=15,
            policy_id="SEC-POL-DEFAULT",
            policy_name="Default Sandbox Policy",
            rule_matched="default_fallback",
        )
