"""Create to-do: the panel's "Add To-Do" form (`todo/add`), then the description through `todo/{id}/update`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import compact, panel, parse_date, time_24
from contractor_foreman_api_mcp.contractor_foreman.tools._todos import EXAMPLE_TODO, PRIORITIES, read_todo
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "What has to be done."},
        "project_id": {"type": "string", "pattern": "^[0-9]+$", "description": "Project from list_projects."},
        "due_date": {"type": "string", "format": "date"},
        "due_time": {"type": "string", "description": "e.g. 09:00 or 2:30 PM."},
        "priority": {"type": "string", "enum": list(PRIORITIES), "default": "medium"},
        "description": {"type": "string"},
        "assignee_ids": {
            "type": "array",
            "items": {"type": "string", "pattern": "^[0-9]+$"},
            "description": "contact_id values from list_contacts of the employees or contacts who should do it.",
        },
    },
    "required": ["name"],
    "additionalProperties": False,
}


@tool(
    name="create_todo",
    title="Create to-do",
    access="write",
    confirm=True,
    description="New to-do, optionally on a project, with due date, priority and assignees.",
    details=(
        "Adds a to-do and returns it as get_todo shows it. Assignees see it in their Contractor Foreman "
        "app. By default you confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /todos",
    example_response=EXAMPLE_TODO,
)
async def create_todo(ctx: ToolContext, args: dict[str, Any]) -> Any:
    name = args["name"].strip()
    if not name:
        raise ToolError("name must not be empty.", ErrorCode.INVALID_INPUT)
    payload = compact(
        {
            "task_name": name,
            "project_id": args.get("project_id"),
            "due_date": parse_date(args["due_date"], "due_date").isoformat() if args.get("due_date") else None,
            "due_time": time_24(args["due_time"], "due_time") if args.get("due_time") else None,
            "priority": PRIORITIES[args.get("priority") or "medium"],
            "access_to_custom_fields": 0,
        }
    )
    if args.get("assignee_ids"):
        payload["assigned_to"] = [int(user_id) for user_id in args["assignee_ids"]]
    body = await panel(ctx, "todo/add", payload)
    todo_id = str((body.get("data") or {}).get("todo_id") or "")
    if not todo_id:
        raise ToolError("Contractor Foreman did not return the new to-do.", ErrorCode.TARGET_ERROR)
    if args.get("description"):
        await panel(ctx, f"todo/{todo_id}/update", {"description": args["description"]})
    return await read_todo(ctx, todo_id)
