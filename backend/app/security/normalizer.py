"""Action Normalizer for autonomous AI agent tool calls in SentraFlow.

Transforms heterogeneous agent tool calls (LangChain, AutoGen, CrewAI, raw commands)
into standardized AgentAction objects without executing them.
"""

import re
from typing import Any, Dict, Optional, Union
from app.schemas.action import ActionType, AgentAction


class ActionNormalizer:
    """Normalizes raw agent tool invocations into standardized AgentAction representations."""

    # Map tool name prefixes/aliases to ActionType
    _TOOL_MAPPING = {
        # File Read
        "read_file": ActionType.READ,
        "read": ActionType.READ,
        "file_read": ActionType.READ,
        "cat": ActionType.READ,
        "view_file": ActionType.READ,
        "get_file_contents": ActionType.READ,
        "read_file_content": ActionType.READ,
        
        # File Write / Edit
        "write_file": ActionType.WRITE,
        "write": ActionType.WRITE,
        "file_write": ActionType.WRITE,
        "create_file": ActionType.WRITE,
        "edit_file": ActionType.WRITE,
        "append_file": ActionType.WRITE,
        "replace_file_content": ActionType.WRITE,
        "save_file": ActionType.WRITE,
        
        # Command / Script Execution
        "bash": ActionType.EXECUTE,
        "shell": ActionType.EXECUTE,
        "sh": ActionType.EXECUTE,
        "terminal": ActionType.EXECUTE,
        "run_command": ActionType.EXECUTE,
        "execute_command": ActionType.EXECUTE,
        "cmd": ActionType.EXECUTE,
        "exec": ActionType.EXECUTE,
        "system_command": ActionType.EXECUTE,
        "python": ActionType.EXECUTE,
        "python_repl": ActionType.EXECUTE,
        "py_eval": ActionType.EXECUTE,
        "code_interpreter": ActionType.EXECUTE,
        "execute_script": ActionType.EXECUTE,
        
        # Network / Web
        "web_search": ActionType.NETWORK_CALL,
        "search_web": ActionType.NETWORK_CALL,
        "http_request": ActionType.NETWORK_CALL,
        "fetch": ActionType.NETWORK_CALL,
        "curl": ActionType.NETWORK_CALL,
        "api_call": ActionType.NETWORK_CALL,
        "get_url": ActionType.NETWORK_CALL,
        "post_url": ActionType.NETWORK_CALL,
        "read_url_content": ActionType.NETWORK_CALL,
        
        # Database / SQL
        "sql_query": ActionType.READ,
        "execute_sql": ActionType.EXECUTE,
        "db_query": ActionType.READ,
        "sql_db_query": ActionType.READ,
        "database_query": ActionType.READ,
        "run_sql": ActionType.EXECUTE,
        
        # Deletion
        "delete_file": ActionType.DELETE,
        "remove_file": ActionType.DELETE,
        "rm": ActionType.DELETE,
        
        # Auth / IAM
        "authenticate": ActionType.AUTH,
        "login": ActionType.AUTH,
        "assume_role": ActionType.AUTH,
    }

    @classmethod
    def normalize(
        cls,
        tool_name: str,
        tool_args: Optional[Union[Dict[str, Any], str]] = None,
        agent_id: str = "agent-generic",
        task: str = "Execute tool action",
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentAction:
        """Normalizes an agent tool invocation into an AgentAction.
        
        Args:
            tool_name: The name of the tool called by the agent.
            tool_args: Arguments passed to the tool (dict or string).
            agent_id: Identifier of the invoking agent.
            task: The high-level task/goal the agent is executing.
            context: Additional execution context metadata.
            
        Returns:
            A normalized AgentAction instance with standardized action and target resource.
        """
        clean_name = (tool_name or "").strip().lower()
        args_dict: Dict[str, Any] = {}
        raw_string_arg: Optional[str] = None

        if isinstance(tool_args, dict):
            args_dict = dict(tool_args)
        elif isinstance(tool_args, str):
            raw_string_arg = tool_args
            args_dict = {"input": tool_args}
        elif tool_args is not None:
            args_dict = {"value": tool_args}

        # Resolve ActionType
        action_type = cls._TOOL_MAPPING.get(clean_name)
        if not action_type:
            # Fallback heuristic classification
            if any(k in clean_name for k in ["read", "get", "fetch", "view", "find", "list", "cat"]):
                action_type = ActionType.READ
            elif any(k in clean_name for k in ["write", "create", "edit", "save", "update", "put", "patch"]):
                action_type = ActionType.WRITE
            elif any(k in clean_name for k in ["delete", "remove", "drop", "destroy", "rm"]):
                action_type = ActionType.DELETE
            elif any(k in clean_name for k in ["exec", "run", "bash", "cmd", "eval", "interpret"]):
                action_type = ActionType.EXECUTE
            elif any(k in clean_name for k in ["http", "url", "net", "web", "search", "request", "curl"]):
                action_type = ActionType.NETWORK_CALL
            elif any(k in clean_name for k in ["auth", "login", "token", "cred", "key"]):
                action_type = ActionType.AUTH
            else:
                action_type = ActionType.OTHER

        # Resolve Resource Target
        resource = cls._extract_resource(clean_name, action_type, args_dict, raw_string_arg)

        # SQL Write / Destructive override
        if clean_name in ["sql_query", "db_query", "database_query", "sql_db_query"] or "sql" in clean_name:
            query_content = str(args_dict.get("query") or args_dict.get("sql") or raw_string_arg or "").upper()
            if any(kw in query_content for kw in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]):
                action_type = ActionType.WRITE if "DROP" not in query_content else ActionType.DELETE

        return AgentAction(
            agent_id=agent_id,
            task=task,
            action=action_type.value,
            resource=resource,
            parameters=args_dict,
            context=context or {},
            action_type=action_type,
        )

    @classmethod
    def _extract_resource(
        cls,
        tool_name: str,
        action_type: ActionType,
        args_dict: Dict[str, Any],
        raw_string_arg: Optional[str],
    ) -> str:
        """Extracts the primary target resource from tool arguments."""
        # 1. Direct path / filename keys
        for key in ["file_path", "filepath", "path", "filename", "target_file", "file", "uri"]:
            if key in args_dict and args_dict[key]:
                return str(args_dict[key]).strip()

        # 2. Command / Script keys
        for key in ["command", "cmd", "script", "code", "input", "query", "sql", "url"]:
            if key in args_dict and args_dict[key]:
                return str(args_dict[key]).strip()

        # 3. Raw string argument
        if raw_string_arg:
            return raw_string_arg.strip()

        # 4. Fallback from first string parameter
        for val in args_dict.values():
            if isinstance(val, str) and val.strip():
                return val.strip()

        # 5. Default generic resource placeholder
        return f"{tool_name}_target"


# Helper instance & function
normalizer = ActionNormalizer()


def normalize_tool_call(
    tool_name: str,
    tool_args: Optional[Union[Dict[str, Any], str]] = None,
    agent_id: str = "agent-generic",
    task: str = "Execute tool action",
    context: Optional[Dict[str, Any]] = None,
) -> AgentAction:
    """Convenience functional wrapper for ActionNormalizer.normalize."""
    return ActionNormalizer.normalize(
        tool_name=tool_name,
        tool_args=tool_args,
        agent_id=agent_id,
        task=task,
        context=context,
    )
