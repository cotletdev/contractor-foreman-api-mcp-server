"""Update to-do: the inline fields of a to-do (`todo/{id}/update`), status included (complete = 66)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import compact, panel, parse_date, time_24
from contractor_foreman_api_mcp.contractor_foreman.tools._todos import (
    EXAMPLE_TODO,
    PRIORITIES,
    STATUSES,
    TODO_ID,
    read_todo,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "todo_id": TODO_ID,
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "due_date": {"type": "string", "format": "date"},
        "due_time": {"type": "string", "description": "e.g. 09:00 or 2:30 PM."},
        "priority": {"type": "string", "enum": list(PRIORITIES)},
        "status": {"type": "string", "enum": list(STATUSES), "description": "complete closes the to-do."},
    },
    "required": ["todo_id"],
    "additionalProperties": False,
}


@tool(
    name="update_todo",
    title="Update to-do",
    access="write",
    description="Change a to-do's name, description, due date, priority or status, e.g. mark it complete.",
    details=(
        "Changes only the fields you pass and returns the to-do as get_todo shows it. status complete closes "
        "it, open reopens it. Assignees and checklist items are not changed. Nothing is sent to anyone, so "
        "this tool runs without asking."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /todos/{todo_id}",
    example_response={**EXAMPLE_TODO, "status": "complete"},
)
async def update_todo(ctx: ToolContext, args: dict[str, Any]) -> Any:
    todo_id = args["todo_id"]
    fields = compact(
        {
            "task_name": (args.get("name") or "").strip(),
            "description": args.get("description"),
            "due_date": parse_date(args["due_date"], "due_date").isoformat() if args.get("due_date") else None,
            "due_time": time_24(args["due_time"], "due_time") if args.get("due_time") else None,
            "priority": PRIORITIES.get(args.get("priority") or ""),
            "status": STATUSES.get(args.get("status") or ""),
        }
    )
    if not fields:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    await read_todo(ctx, todo_id)
    await panel(ctx, f"todo/{todo_id}/update", fields)
    return await read_todo(ctx, todo_id)
