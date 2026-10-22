"""Get to-do: one to-do (`todo/{id}/get-todo-detail`) with its checklist (`todo/{id}/get-check-list`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._todos import EXAMPLE_TODO, TODO_ID, read_todo
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"todo_id": TODO_ID},
    "required": ["todo_id"],
    "additionalProperties": False,
}


@tool(
    name="get_todo",
    title="Get to-do",
    access="read",
    description="One to-do: description, project, priority, status, due date, assignees and checklist.",
    details="Returns one to-do with its description, due date and time, assignees and checklist items. Read only.",
    input_schema=INPUT_SCHEMA,
    route="GET /todos/{todo_id}",
    example_response=EXAMPLE_TODO,
)
async def get_todo(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_todo(ctx, args["todo_id"])
