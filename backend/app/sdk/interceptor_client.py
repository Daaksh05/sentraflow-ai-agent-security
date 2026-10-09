"""SentraFlow Interception Client & Decorator SDK.

Provides synchronous and asynchronous clients for external agent frameworks (LangChain, AutoGen, CrewAI)
to query SentraFlow before executing tool operations.
"""

from functools import wraps
import inspect
from typing import Any, Callable, Dict, List, Optional, Union
import httpx

from app.schemas.action import ActionContext, AgentAction, BatchAgentActionRequest
from app.schemas.security import (
    BatchSecurityDecisionResponse,
    DecisionOutcome,
    SecurityDecision,
)
from app.security.normalizer import normalizer


class SentraFlowSecurityException(Exception):
    """Raised when an agent action is blocked by SentraFlow policy or AI intent evaluation."""

    def __init__(self, decision: SecurityDecision):
        self.decision = decision
        super().__init__(
            f"SentraFlow BLOCKED action '{decision.intent}' (Risk: {decision.risk_score}/100): {decision.reason}"
        )


class SentraFlowClient:
    """Python SDK client for interacting with the SentraFlow Security Control Plane."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_prefix: str = "/api/v1",
        timeout: float = 10.0,
        raise_on_block: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = api_prefix
        self.timeout = timeout
        self.raise_on_block = raise_on_block
        self._analyze_endpoint = f"{self.base_url}{self.api_prefix}/analyze"
        self._batch_endpoint = f"{self.base_url}{self.api_prefix}/analyze/batch"

    # --- Synchronous Interception Methods ---

    def analyze_action(
        self,
        action: Union[AgentAction, Dict[str, Any]],
        context: Optional[Union[ActionContext, Dict[str, Any]]] = None,
    ) -> SecurityDecision:
        """Synchronously intercepts and evaluates an agent action against SentraFlow policies."""
        payload = self._format_action_payload(action, context)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self._analyze_endpoint, json=payload)
            response.raise_for_status()
            decision = SecurityDecision.model_validate(response.json())

        if self.raise_on_block and decision.decision == DecisionOutcome.BLOCK:
            raise SentraFlowSecurityException(decision)

        return decision

    def analyze_tool_call(
        self,
        tool_name: str,
        tool_args: Optional[Union[Dict[str, Any], str]] = None,
        agent_id: str = "agent-sdk",
        task: str = "Execute tool operation",
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityDecision:
        """Normalizes a raw tool call and evaluates it in one call."""
        normalized_action = normalizer.normalize(
            tool_name=tool_name,
            tool_args=tool_args,
            agent_id=agent_id,
            task=task,
            context=context,
        )
        return self.analyze_action(normalized_action)

    def analyze_batch(
        self,
        actions: List[Union[AgentAction, Dict[str, Any]]],
        context: Optional[Union[ActionContext, Dict[str, Any]]] = None,
        stop_on_first_block: bool = False,
    ) -> BatchSecurityDecisionResponse:
        """Synchronously evaluates a batch of planned agent actions."""
        batch_actions = [
            a if isinstance(a, AgentAction) else AgentAction.model_validate(a)
            for a in actions
        ]
        parsed_context = (
            context
            if isinstance(context, ActionContext) or context is None
            else ActionContext.model_validate(context)
        )
        batch_request = BatchAgentActionRequest(
            actions=batch_actions,
            context=parsed_context,
            stop_on_first_block=stop_on_first_block,
        )

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self._batch_endpoint, json=batch_request.model_dump(mode="json"))
            response.raise_for_status()
            return BatchSecurityDecisionResponse.model_validate(response.json())

    # --- Asynchronous Interception Methods ---

    async def analyze_action_async(
        self,
        action: Union[AgentAction, Dict[str, Any]],
        context: Optional[Union[ActionContext, Dict[str, Any]]] = None,
    ) -> SecurityDecision:
        """Asynchronously intercepts and evaluates an agent action."""
        payload = self._format_action_payload(action, context)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self._analyze_endpoint, json=payload)
            response.raise_for_status()
            decision = SecurityDecision.model_validate(response.json())

        if self.raise_on_block and decision.decision == DecisionOutcome.BLOCK:
            raise SentraFlowSecurityException(decision)

        return decision

    async def analyze_batch_async(
        self,
        actions: List[Union[AgentAction, Dict[str, Any]]],
        context: Optional[Union[ActionContext, Dict[str, Any]]] = None,
        stop_on_first_block: bool = False,
    ) -> BatchSecurityDecisionResponse:
        """Asynchronously evaluates a batch of planned agent actions."""
        batch_actions = [
            a if isinstance(a, AgentAction) else AgentAction.model_validate(a)
            for a in actions
        ]
        parsed_context = (
            context
            if isinstance(context, ActionContext) or context is None
            else ActionContext.model_validate(context)
        )
        batch_request = BatchAgentActionRequest(
            actions=batch_actions,
            context=parsed_context,
            stop_on_first_block=stop_on_first_block,
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._batch_endpoint, json=batch_request.model_dump(mode="json")
            )
            response.raise_for_status()
            return BatchSecurityDecisionResponse.model_validate(response.json())

    def _format_action_payload(
        self,
        action: Union[AgentAction, Dict[str, Any]],
        context: Optional[Union[ActionContext, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if isinstance(action, AgentAction):
            payload = action.model_dump(mode="json")
        else:
            payload = dict(action)

        if context is not None:
            if isinstance(context, ActionContext):
                payload["action_context"] = context.model_dump(mode="json")
            else:
                payload["action_context"] = dict(context)

        return payload


def guard_action(
    client: Optional[SentraFlowClient] = None,
    agent_id: str = "agent-guard",
    task: str = "Protected Tool Invocation",
    tool_name: Optional[str] = None,
):
    """Decorator for intercepting tool functions with SentraFlow before execution.
    
    If SentraFlow issues a BLOCK verdict, raises SentraFlowSecurityException.
    """
    sf_client = client or SentraFlowClient(raise_on_block=True)

    def decorator(func: Callable):
        t_name = tool_name or func.__name__

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                args_dict = dict(kwargs)
                if args:
                    args_dict["positional_args"] = [str(a) for a in args]

                decision = await sf_client.analyze_action_async(
                    normalizer.normalize(
                        tool_name=t_name,
                        tool_args=args_dict,
                        agent_id=agent_id,
                        task=task,
                    )
                )
                if decision.decision == DecisionOutcome.BLOCK:
                    raise SentraFlowSecurityException(decision)
                return await func(*args, **kwargs)

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                args_dict = dict(kwargs)
                if args:
                    args_dict["positional_args"] = [str(a) for a in args]

                decision = sf_client.analyze_action(
                    normalizer.normalize(
                        tool_name=t_name,
                        tool_args=args_dict,
                        agent_id=agent_id,
                        task=task,
                    )
                )
                if decision.decision == DecisionOutcome.BLOCK:
                    raise SentraFlowSecurityException(decision)
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator
