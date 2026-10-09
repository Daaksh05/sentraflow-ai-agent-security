"""Structured logging configuration for SentraFlow security events."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONSecurityFormatter(logging.Formatter):
    """Formats log records as structured JSON suitable for SIEM/audit pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom security attributes if present
        if hasattr(record, "security_event"):
            log_obj["security_event"] = getattr(record, "security_event")

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures root and application loggers."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if re-initialized
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONSecurityFormatter())
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(JSONSecurityFormatter())

    # Create dedicated security audit logger
    security_logger = logging.getLogger("sentraflow.security")
    security_logger.setLevel(level)
    return security_logger


logger = logging.getLogger("sentraflow")
security_logger = logging.getLogger("sentraflow.security")


def log_security_event(
    agent_id: str,
    action: str,
    resource: str,
    decision: str,
    risk_score: float,
    reason: str,
    request_id: str,
    extra_context: Optional[Dict[str, Any]] = None,
    policy_rationale: Optional[str] = None,
    response_mode: str = "decision",
    response_outcome: str = "decision_returned_to_caller",
    recommended_response: Optional[str] = None,
) -> None:
    """Emits a structured audit log entry for every intercepted agent action and security decision."""
    event_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "action": action,
        "resource": resource,
        "decision": decision,
        "risk_score": risk_score,
        "reason": reason,
        "request_id": request_id,
        "policy_rationale": policy_rationale,
        "response_mode": response_mode,
        "response_outcome": response_outcome,
        "recommended_response": recommended_response,
        "extra_context": extra_context or {},
    }
    
    security_logger.info(
        f"Security Decision: agent={agent_id} action={action} decision={decision} risk={risk_score}",
        extra={"security_event": event_data},
    )
