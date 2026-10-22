"""List schedule tasks: the project's Schedule tab, a Gantt chart (`projects/gantt-chart-data`, key `project`).

Task ids look like `task_7570485`. The chart's first row (`prj_<project>`) is the project itself and is left
out. `start_date` is the first day; the chart's `temp_end_date` is the day after the last (exclusive end),
`full_end_date` the last day itself. Links are finish-to-start (type 0) unless the type says otherwise.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import iso, number, panel, text
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import PROJECT_ID
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# dhtmlx Gantt link types.
LINK_TYPES = {0: "finish_to_start", 1: "start_to_start", 2: "finish_to_finish", 3: "start_to_finish"}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"project_id": PROJECT_ID},
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "project_id": "1678164",
    "tasks": [
        {
            "task_id": "task_7570477",
            "name": "Rough In Plumbing",
            "kind": "task",
            "parent_task_id": None,
            "start_date": "2021-12-29",
            "end_date": "2022-01-17",
            "duration_days": 20,
            "percent_complete": 58.0,
            "assignees": ["Scott Carli"],
            "depends_on": [{"task_id": "task_7570476", "type": "finish_to_start", "lag_days": 0}],
        }
    ],
}


async def gantt(ctx: ToolContext, project_id: str) -> dict[str, Any]:
    """The raw chart answer: `data` (rows) and `collections.links`."""
    return await panel(ctx, "projects/gantt-chart-data", {"project": project_id, "module_key": "projects"})


def is_root(parent: Any, project_id: str) -> bool:
    return str(parent or "0") in ("0", f"prj_{project_id}", f"task_{project_id}")


def task_view(row: dict[str, Any], links: list[dict[str, Any]], project_id: str) -> dict[str, Any]:
    task_id = str(row.get("id"))
    names = [
        text(user.get("assignee_name")) for user in (row.get("task_users") or []) + (row.get("assignees_to") or [])
    ]
    kind = row.get("type") or "task"
    return {
        "task_id": task_id,
        "name": text(row.get("text")),
        "kind": "summary" if kind == "project" else kind,
        "parent_task_id": None if is_root(row.get("parent"), project_id) else str(row.get("parent")),
        "start_date": iso(row.get("start_date")),
        "end_date": iso(row.get("full_end_date")) or iso(row.get("start_date")),
        "duration_days": int(number(row.get("duration"))),
        "percent_complete": round(number(row.get("progress")) * 100, 1),
        "assignees": [name for name in names if name],
        "depends_on": [
            {
                "task_id": str(link.get("source")),
                "type": LINK_TYPES.get(int(number(link.get("type"))), "finish_to_start"),
                "lag_days": int(number(link.get("lag"))),
            }
            for link in links
            if str(link.get("target")) == task_id
        ],
    }


def task_rows(body: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
    links = (body.get("collections") or {}).get("links") or []
    return [
        task_view(row, links, project_id)
        for row in body.get("data") or []
        if not str(row.get("id", "")).startswith("prj_") and str(row.get("project_id")) == project_id
    ]


@tool(
    name="list_schedule_tasks",
    title="List schedule tasks",
    access="read",
    description="Gantt schedule tasks of a project: dates, duration, dependencies, assignees, percent complete.",
    details=(
        "Returns the tasks of the project schedule in Gantt order. kind is task, milestone or summary (a "
        "group whose dates follow its subtasks). end_date is the task's last day, inclusive. depends_on "
        "lists the tasks this one waits for, with the link type and lag in days. Use task_id with "
        "update_schedule_task. An empty list means the project has no schedule yet."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/{project_id}/schedule-tasks",
    example_response=EXAMPLE_RESPONSE,
)
async def list_schedule_tasks(ctx: ToolContext, args: dict[str, Any]) -> Any:
    project_id = args["project_id"]
    return {"project_id": project_id, "tasks": task_rows(await gantt(ctx, project_id), project_id)}
