"""Unit tests for ActionNormalizer tool call standardization."""

import pytest
from app.schemas.action import ActionType
from app.security.normalizer import ActionNormalizer, normalize_tool_call


def test_normalize_read_file_tool():
    action = normalize_tool_call(
        tool_name="read_file",
        tool_args={"file_path": "./src/main.py"},
        agent_id="agent-coder",
        task="Read source code",
    )
    assert action.action == ActionType.READ.value
    assert action.resource == "./src/main.py"
    assert action.agent_id == "agent-coder"
    assert action.action_type == ActionType.READ


def test_normalize_write_file_tool():
    action = normalize_tool_call(
        tool_name="write_file",
        tool_args={"path": "/app/output.txt", "content": "hello world"},
        agent_id="agent-writer",
        task="Write output",
    )
    assert action.action == ActionType.WRITE.value
    assert action.resource == "/app/output.txt"
    assert action.action_type == ActionType.WRITE


def test_normalize_bash_shell_command():
    action = normalize_tool_call(
        tool_name="bash",
        tool_args={"command": "rm -rf /"},
        agent_id="agent-destroyer",
        task="Cleanup directory",
    )
    assert action.action == ActionType.EXECUTE.value
    assert action.resource == "rm -rf /"
    assert action.action_type == ActionType.EXECUTE


def test_normalize_python_execution():
    action = normalize_tool_call(
        tool_name="python_repl",
        tool_args="import os; os.listdir('.')",
        agent_id="agent-repl",
        task="Inspect directory",
    )
    assert action.action == ActionType.EXECUTE.value
    assert action.resource == "import os; os.listdir('.')"
    assert action.action_type == ActionType.EXECUTE


def test_normalize_web_search():
    action = normalize_tool_call(
        tool_name="web_search",
        tool_args={"query": "FastAPI security best practices"},
        agent_id="agent-research",
        task="Research security",
    )
    assert action.action == ActionType.NETWORK_CALL.value
    assert action.resource == "FastAPI security best practices"
    assert action.action_type == ActionType.NETWORK_CALL


def test_normalize_database_sql_query_read():
    action = normalize_tool_call(
        tool_name="sql_query",
        tool_args={"query": "SELECT * FROM users WHERE active = true"},
        agent_id="agent-db",
        task="Fetch users",
    )
    assert action.action == ActionType.READ.value
    assert action.resource == "SELECT * FROM users WHERE active = true"


def test_normalize_database_sql_query_destructive():
    action = normalize_tool_call(
        tool_name="sql_query",
        tool_args={"query": "DROP TABLE users CASCADE"},
        agent_id="agent-db",
        task="Drop table",
    )
    assert action.action == ActionType.DELETE.value
    assert "DROP TABLE users CASCADE" in action.resource


def test_normalize_delete_file():
    action = normalize_tool_call(
        tool_name="delete_file",
        tool_args={"target_file": "/tmp/cache.tmp"},
    )
    assert action.action == ActionType.DELETE.value
    assert action.resource == "/tmp/cache.tmp"
