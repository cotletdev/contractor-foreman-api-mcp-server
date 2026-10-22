"""List to-dos: the To-Do list (`todo`, `start`/`limit`, filter by project, assignee, status, mine)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import panel
from contractor_foreman_api_mcp.contractor_foreman.tools._todos import EXAMPLE_TODO, STATUSES, todo_view
from contractor_foreman_api_mcp.core.helpers import limit
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "pattern": "^[0-9]+$", "description": "Only to-dos of this project."},
        "status": {"type": "string", "enum": list(STATUSES)},
        "mine_only": {
            "type": "boolean",
            "default": False,
            "description": "Only to-dos assigned to this account's user.",
        },
        "search": {"type": "string", "description": "Text to match, as the search box of the To-Do list."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "todos": [
        {
            key: value
            for key, value in EXAMPLE_TODO.items()
            if key not in ("checklist", "due_time", "created_by", "created_date", "completed_date", "description")
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_todos",
    title="List to-dos",
    access="read",
    description="To-dos with project, priority, status, due date and assignees.",
    details=(
        "Returns to-dos, optionally for one project, one status (open, incomplete, complete) or only those "
        "assigned to you. get_todo gives one with its description and checklist. Pages hold up to 100 "
        "to-dos; pass next_cursor back as cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /todos",
    example_response=EXAMPLE_RESPONSE,
)
async def list_todos(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 30, 100)
    cursor = args.get("cursor")
    start = int(cursor) if cursor and cursor.isdigit() else 0
    todo_filter: dict[str, Any] = {"is_my_todo": 1 if args.get("mine_only") else 0}
    if args.get("project_id"):
        todo_filter["project"] = args["project_id"]
    if args.get("status"):
        todo_filter["status"] = STATUSES[args["status"]]
    payload: dict[str, Any] = {"limit": size, "start": start, "ignore_filter": 1, "filter": todo_filter}
    if args.get("search"):
        payload["search"] = args["search"]
    rows = (await panel(ctx, "todo", payload)).get("data") or []
    todos = []
    for row in rows:
        view = todo_view(row)
        todos.append({key: view[key] for key in EXAMPLE_RESPONSE["todos"][0]})
    return {"todos": todos, "next_cursor": str(start + size) if len(rows) == size else None}
