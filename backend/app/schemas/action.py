"""Schemas defining Agent Action and Execution Context."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Standardized categories of actions that an autonomous agent can request."""
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    NETWORK_CALL = "NETWORK_CALL"
    AUTH = "AUTH"
    DELETE = "DELETE"
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    OTHER = "OTHER"


class PreviousAction(BaseModel):
    """Record of a previously executed action in the agent's session."""
    action: str
    resource: str
    decision: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActionContext(BaseModel):
    """Rich execution context surrounding the requested action for policy and intent evaluation."""
    agent_id: Optional[str] = Field(default=None, description="Identifier of the executing agent")
    task: Optional[str] = Field(default=None, description="High-level goal or task context")
    requested_action: Optional[str] = Field(default=None, description="Action verb name")
    target_resource: Optional[str] = Field(default=None, description="Target resource path or URI")
    session_id: Optional[str] = Field(default=None, description="Correlation session identifier")
    previous_actions: List[PreviousAction] = Field(default_factory=list, description="Recent action history in the current session")
    permissions: List[str] = Field(default_factory=list, description="Declared permissions / roles granted to this agent")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Sanitized environment details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata passed by the host system or agent runtime")


class AgentAction(BaseModel):
    """Represents a specific atomic action requested by an autonomous AI agent."""
    agent_id: str = Field(..., description="Unique identifier of the agent requesting the action", examples=["agent-001"])
    task: str = Field(..., description="The high-level goal or prompt given to the agent", examples=["Fix failing tests"])
    action: str = Field(..., description="Requested operation (e.g., READ, WRITE, EXECUTE, or specific tool call)", examples=["READ"])
    resource: str = Field(..., description="Target file path, API endpoint, database table, or system resource", examples=["./tests/test_auth.py"])
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parameters or payload associated with the action")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution environment or agent state metadata")
    action_context: Optional[ActionContext] = Field(default=None, description="Structured execution context for policy and intent evaluation")
    action_type: Optional[ActionType] = Field(default=None, description="Normalized ActionType enum category")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the action was intercepted")


class BatchAgentActionRequest(BaseModel):
    """Request payload for evaluating multiple planned agent actions in a single batch."""
    actions: List[AgentAction] = Field(..., min_length=1, description="List of planned agent actions to analyze")
    context: Optional[ActionContext] = Field(default=None, description="Shared session or execution context")
    stop_on_first_block: bool = Field(default=False, description="Whether to short-circuit evaluation upon encountering the first BLOCK verdict")
