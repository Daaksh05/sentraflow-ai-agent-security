"""Database connection, session management, and audit persistence for SentraFlow."""

import logging
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.models.database import Base, SecurityAuditLogModel
from app.schemas.action import AgentAction
from app.schemas.security import SecurityDecision

logger = logging.getLogger("sentraflow.database")

# Secret keys to sanitize before persistence
SENSITIVE_KEY_PATTERNS = {
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "bearer",
    "credential",
    "credentials",
    "private_key",
    "secret_key",
}


def sanitize_dict(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Recursively redacts sensitive keys and values from dictionary payloads."""
    if not data or not isinstance(data, dict):
        return {}

    sanitized: Dict[str, Any] = {}
    for k, v in data.items():
        k_lower = str(k).lower()
        if any(pattern in k_lower for pattern in SENSITIVE_KEY_PATTERNS):
            sanitized[k] = "[REDACTED_SECRET]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [
                sanitize_dict(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized


# Create Async SQLAlchemy Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Async Session Factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    """FastAPI dependency for yielding async database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> bool:
    """Initializes database tables if connection is available."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified and initialized successfully.")
        return True
    except Exception as exc:
        logger.warning(f"Database initialization skipped or deferred: {exc}")
        return False


async def persist_security_audit_log(
    action: AgentAction,
    decision: SecurityDecision,
    session: Optional[AsyncSession] = None,
) -> Optional[SecurityAuditLogModel]:
    """Persists a sanitized security evaluation record into PostgreSQL.
    
    Ensures that secrets are strictly redacted and database errors do not disrupt
    the synchronous interception critical path.
    """
    try:
        sanitized_parameters = sanitize_dict(action.parameters)
        sanitized_context = sanitize_dict(action.context)
        
        details = {
            "parameters": sanitized_parameters,
            "context": sanitized_context,
            "enforcement_mode": decision.enforcement_mode,
            "policy_rule_matched": decision.policy_decision.rule_matched if decision.policy_decision else None,
            "ai_risk_indicators": decision.intent_analysis.risk_indicators if decision.intent_analysis else [],
            "ai_confidence": decision.intent_analysis.confidence if decision.intent_analysis else None,
        }

        audit_record = SecurityAuditLogModel(
            request_id=decision.request_id,
            agent_id=action.agent_id,
            task=action.task,
            action=action.action,
            resource=action.resource,
            decision=decision.decision.value,
            risk_score=decision.risk_score,
            reason=decision.reason,
            intent=decision.intent,
            analysis_source=decision.analysis_source,
            details=details,
            created_at=decision.evaluated_at,
        )

        if session is not None:
            session.add(audit_record)
            await session.commit()
            await session.refresh(audit_record)
            return audit_record

        async with async_session_factory() as local_session:
            async with local_session.begin():
                local_session.add(audit_record)
            return audit_record

    except Exception as exc:
        logger.warning(
            f"Could not persist audit log for request_id={decision.request_id} to database: {exc}"
        )
        return None
