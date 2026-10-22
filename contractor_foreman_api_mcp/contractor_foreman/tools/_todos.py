"""To-do shapes shared by the to-do tools (`/api/todo/*`, recorded 21.10.2026).

Priority and status are global type ids (`global/types`): priority critical 60, high 57, medium 58, low 59;
status open 64, incomplete 65, complete 66. `todo/{id}/update` takes any subset of the add fields plus
`description` and `status`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import iso, panel, text
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

PRIORITIES = {"critical": "60", "high": "57", "medium": "58", "low": "59"}
STATUSES = {"open": "64", "incomplete": "65", "complete": "66"}
TODO_ID = {"type": "string", "pattern": "^[0-9]+$", "description": "todo_id from list_todos."}

EXAMPLE_TODO: dict[str, Any] = {
    "todo_id": "673971",
    "name": "Order cabinets from supplier",
    "description": "Confirm the shaker white SKU list with the homeowner before ordering.",
    "project_id": "1678216",
    "project_name": "Kitchen remodel - Oak St",
    "priority": "medium",
    "status": "open",
    "due_date": "2026-10-31",
    "due_time": "09:00 AM",
    "completed_date": None,
    "assignees": ["Scott Carli"],
    "created_by": "Michael Howard",
    "created_date": "2026-10-21",
    "checklist": [{"task": "Get final SKU list signed", "done": False}],
}


def _key(names: dict[str, str], type_id: Any, fallback: Any) -> str | None:
    for name, value in names.items():
        if str(type_id) == value:
            return name
    return text(fallback)


def todo_view(data: dict[str, Any], checklist: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    people = data.get("assigneeDetail") or data.get("assigned_to") or []
    view = {
        "todo_id": str(data.get("todo_id")),
        "name": text(data.get("task_name")),
        "description": text(data.get("description")),
        "project_id": None if str(data.get("project_id") or "0") == "0" else str(data.get("project_id")),
        "project_name": text(data.get("project_name")),
        "priority": _key(PRIORITIES, data.get("priority"), data.get("priority_key")),
        "status": _key(STATUSES, data.get("status"), data.get("status_key")),
        "due_date": iso(data.get("due_date")),
        "due_time": text(data.get("due_time")),
        "completed_date": iso(data.get("completed_date")),
        "assignees": [
            name
            for name in (
                text(person.get("assignee_name") or person.get("display_name"))
                for person in people
                if isinstance(person, dict)
            )
            if name
        ],
        "created_by": text(data.get("full_name")),
        "created_date": iso(data.get("date_added")),
    }
    if checklist is not None:
        view["checklist"] = checklist
    return view


async def read_todo(ctx: ToolContext, todo_id: str) -> dict[str, Any]:
    body = await panel(ctx, f"todo/{todo_id}/get-todo-detail", {})
    data = body.get("data")
    if not isinstance(data, dict) or not data.get("todo_id"):
        raise ToolError(f"No to-do {todo_id} in this account. Use list_todos.", ErrorCode.TARGET_ERROR)
    lists = (await panel(ctx, f"todo/{todo_id}/get-check-list", {})).get("data") or {}
    items = list(lists.get("checklist") or [])
    for section in lists.get("sections") or []:
        items.extend(section.get("tasks") or [])
    checklist = [
        {"task": text(item.get("task")), "done": str(item.get("status")) in ("1", "completed", "true")}
        for item in items
    ]
    return todo_view(data, checklist)
