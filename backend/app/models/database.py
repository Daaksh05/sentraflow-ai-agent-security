"""SQLAlchemy database models foundation for SentraFlow."""

from datetime import datetime, timezone
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SecurityAuditLogModel(Base):
    """Database model storing historical security evaluations and audit events."""

    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    agent_id = Column(String(128), index=True, nullable=False)
    task = Column(Text, nullable=False)
    action = Column(String(64), index=True, nullable=False)
    resource = Column(String(512), index=True, nullable=False)
    decision = Column(String(32), index=True, nullable=False)  # ALLOW, BLOCK
    risk_score = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    intent = Column(Text, nullable=True)
    analysis_source = Column(String(64), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
