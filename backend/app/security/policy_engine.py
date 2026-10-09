"""Deterministic Policy Engine foundation for SentraFlow.

Supports dynamic policy profile loading (JSON/dict/file), validation, profile switching,
and ensures mandatory critical safety rules always retain absolute priority.
"""

import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
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
        self.raw_resource_pattern = resource_pattern
        self.raw_action_pattern = action_pattern
        self.resource_pattern = re.compile(resource_pattern, re.IGNORECASE)
        self.action_pattern = re.compile(action_pattern, re.IGNORECASE)
        self.outcome = outcome
        self.risk_score = risk_score
        self.reason = reason

    def matches(self, action: str, resource: str) -> bool:
        # Standard match: action matches action_pattern AND resource matches resource_pattern
        if bool(self.action_pattern.search(action)) and bool(self.resource_pattern.search(resource)):
            return True
        # Cross match: command/pattern present in resource or action verb
        if bool(self.action_pattern.search(resource)) and bool(self.resource_pattern.search(action)):
            return True
        return False


class PolicyEngine:
    """Evaluates deterministic security rules before or alongside AI intent evaluation.
    
    Mandatory safety rules (e.g. credential theft, destruction) always retain evaluation priority
    and cannot be overridden or disabled by loaded custom profiles.
    """

    def __init__(self, rules: Optional[List[PolicyRule]] = None):
        self._critical_rules: List[PolicyRule] = self._get_critical_rules()
        self.active_profile_id: str = "POL-DEFAULT-BUILTIN"
        self.active_profile_name: str = "Built-in Security Baseline"
        self.active_profile_version: str = "1.0"
        
        if rules is not None:
            self._custom_rules: List[PolicyRule] = rules
        else:
            self._custom_rules = self._get_default_custom_rules()
        
        self._rebuild_rules()

    def _get_critical_rules(self) -> List[PolicyRule]:
        """Provides mandatory, non-negotiable critical safety boundary rules."""
        return [
            # Hard block on credential & private key paths
            PolicyRule(
                rule_id="SEC-POL-CRIT-001",
                name="Mandatory Credential & Key Protection",
                resource_pattern=r"(\.env|id_rsa|\.aws/credentials|\.ssh/|secrets\.json|master_secret)",
                action_pattern=r"(READ|WRITE|DELETE|EXECUTE)",
                outcome=DecisionOutcome.BLOCK,
                risk_score=95,
                reason="Direct access to secret keys, AWS credentials, and environment files is strictly prohibited.",
            ),
            # Hard block on system destruction commands
            PolicyRule(
                rule_id="SEC-POL-CRIT-002",
                name="Mandatory System Destruction Prevention",
                resource_pattern=r".*",
                action_pattern=r"(rm\s+-rf\s+/|drop\s+database|format\s+c:)",
                outcome=DecisionOutcome.BLOCK,
                risk_score=100,
                reason="Destructive system commands are blocked by security policy.",
            ),
        ]

    def _get_default_custom_rules(self) -> List[PolicyRule]:
        """Baseline standard custom rules."""
        return [
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

    def _rebuild_rules(self) -> None:
        """Combines critical rules and custom profile rules with critical rules first."""
        self.rules: List[PolicyRule] = list(self._critical_rules) + list(self._custom_rules)

    def validate_policy_dict(self, data: Dict[str, Any]) -> None:
        """Validates that the policy dictionary adheres to the required schema."""
        if not isinstance(data, dict):
            raise ValueError("Policy must be a JSON object / dictionary")
        
        if "rules" not in data or not isinstance(data["rules"], list):
            raise ValueError("Policy definition must contain a 'rules' list")
        
        for idx, rule in enumerate(data["rules"]):
            if not isinstance(rule, dict):
                raise ValueError(f"Rule at index {idx} must be a dictionary")
            
            for required_field in ["resource_pattern", "action_pattern"]:
                if required_field not in rule or not str(rule[required_field]).strip():
                    raise ValueError(f"Rule at index {idx} missing required field '{required_field}'")
            
            # Validate decision/outcome
            outcome_val = rule.get("decision") or rule.get("outcome")
            if not outcome_val:
                raise ValueError(f"Rule at index {idx} must specify 'decision' or 'outcome'")
            
            # Check regex validity
            try:
                re.compile(rule["resource_pattern"])
                re.compile(rule["action_pattern"])
            except re.error as err:
                raise ValueError(f"Rule at index {idx} has invalid regex pattern: {err}")

    def load_from_dict(self, data: Dict[str, Any]) -> int:
        """Loads and activates a policy profile from a dictionary.
        
        Args:
            data: Parsed policy dictionary.
            
        Returns:
            Number of custom rules loaded.
        """
        self.validate_policy_dict(data)

        self.active_profile_id = str(data.get("policy_id", "POL-CUSTOM"))
        self.active_profile_name = str(data.get("name", "Custom Policy Profile"))
        self.active_profile_version = str(data.get("version", "1.0"))

        new_custom_rules: List[PolicyRule] = []
        for idx, r in enumerate(data["rules"]):
            raw_decision = str(r.get("decision") or r.get("outcome", "ALLOW")).upper()
            try:
                outcome = DecisionOutcome(raw_decision)
            except ValueError:
                outcome = DecisionOutcome.ALLOW if "ALLOW" in raw_decision else DecisionOutcome.BLOCK

            risk_score = int(r.get("risk_score", 50 if outcome == DecisionOutcome.BLOCK else 15))
            reason = str(r.get("reason", f"Matched custom rule {r.get('id', idx)}"))

            rule_obj = PolicyRule(
                rule_id=str(r.get("id", f"RULE-{idx + 1:03d}")),
                name=str(r.get("name", f"Custom Rule {idx + 1}")),
                resource_pattern=str(r["resource_pattern"]),
                action_pattern=str(r["action_pattern"]),
                outcome=outcome,
                risk_score=risk_score,
                reason=reason,
            )
            new_custom_rules.append(rule_obj)

        self._custom_rules = new_custom_rules
        self._rebuild_rules()
        logger.info(f"Loaded policy profile '{self.active_profile_name}' with {len(new_custom_rules)} custom rules")
        return len(new_custom_rules)

    def load_from_json(self, json_str: str) -> int:
        """Loads and activates a policy profile from a JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON policy: {exc}")
        return self.load_from_dict(data)

    def load_policy_file(self, file_path: Union[str, Path]) -> int:
        """Loads and activates a policy profile from a file path."""
        target_path = Path(file_path)
        
        # If relative, check directly or relative to repository policies directory
        if not target_path.exists():
            repo_policy_path = Path(__file__).resolve().parent.parent.parent.parent / "policies" / "examples" / target_path.name
            if repo_policy_path.exists():
                target_path = repo_policy_path
            else:
                raise FileNotFoundError(f"Policy file not found: {file_path}")

        try:
            content = target_path.read_text(encoding="utf-8")
        except Exception as exc:
            raise ValueError(f"Failed to read policy file {target_path}: {exc}")

        return self.load_from_json(content)

    def switch_profile(self, profile_identifier: str) -> int:
        """Convenience method to switch policy profile by preset name or path."""
        clean_name = profile_identifier.strip().lower()
        if clean_name in ["default_strict", "strict"]:
            return self.load_policy_file("default_strict.json")
        elif clean_name in ["developer_sandbox", "sandbox", "dev"]:
            return self.load_policy_file("developer_sandbox.json")
        elif clean_name in ["default", "builtin"]:
            return self.reset_to_defaults()
        else:
            return self.load_policy_file(profile_identifier)

    def reset_to_defaults(self) -> int:
        """Resets engine to default baseline rules."""
        self._custom_rules = self._get_default_custom_rules()
        self.active_profile_id = "POL-DEFAULT-BUILTIN"
        self.active_profile_name = "Built-in Security Baseline"
        self.active_profile_version = "1.0"
        self._rebuild_rules()
        return len(self._custom_rules)

    def evaluate(self, action: AgentAction, context: Optional[ActionContext] = None) -> PolicyDecision:
        """Evaluates an AgentAction against active policy rules.
        
        Deterministic policy evaluation ensures absolute boundary control regardless of LLM output.
        Critical rules are always evaluated first.
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
