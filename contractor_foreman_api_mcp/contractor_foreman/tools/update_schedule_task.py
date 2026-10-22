"""Update schedule task: one Gantt edit, sent the way the chart's data processor batches it.

`projects/update-schedule-tasks` takes `{project_id, gantt_data: {tasks: [{entity, action, id, data}], count}}`
(GanttChartView.client, 21.10.2026). `data` is the whole task row with `start_date` and the exclusive `end_date`
as "YYYY-MM-DD HH:mm:ss". The server moves no dependent task; the chart's auto-scheduling does that in the
browser. Saving a task can also move the project's own start and end dates to the schedule's.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import number, panel, parse_date, text
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import PROJECT_ID
from contractor_foreman_api_mcp.contractor_foreman.tools.list_schedule_tasks import EXAMPLE_RESPONSE as TASKS
from contractor_foreman_api_mcp.contractor_foreman.tools.list_schedule_tasks import gantt, task_rows
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": PROJECT_ID,
        "task_id": {"type": "string", "pattern": "^task_[0-9]+$", "description": "task_id from list_schedule_tasks."},
        "name": {"type": "string", "minLength": 1},
        "start_date": {
            "type": "string",
            "format": "date",
            "description": "New first day. Alone, it moves the task and keeps its length.",
        },
        "end_date": {"type": "string", "format": "date", "description": "New last day."},
        "duration_days": {"type": "integer", "minimum": 0, "description": "New length in days, from the start."},
        "percent_complete": {"type": "number", "minimum": 0, "maximum": 100},
    },
    "required": ["project_id", "task_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "project_id": "1678164",
    "task": {**TASKS["tasks"][0], "start_date": "2022-01-03", "end_date": "2022-01-22", "percent_complete": 60.0},
}

# Row fields the chart sends back, minus its display-only lists and names.
_DROP = {"assignees_to", "task_users", "assignee_name", "task_user_name", "contractors", "employees"}


def _day(value: Any) -> date:
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _stamp(value: date) -> str:
    return f"{value.isoformat()} 00:00:00"


def new_dates(row: dict[str, Any], args: dict[str, Any]) -> tuple[date, date]:
    """(start, exclusive end) after the change."""
    start, end = _day(row["start_date"]), _day(row.get("temp_end_date") or row["start_date"])
    length = (end - start).days
    if args.get("start_date"):
        start = parse_date(args["start_date"], "start_date")
        end = start + timedelta(days=length)
    if args.get("end_date"):
        end = parse_date(args["end_date"], "end_date") + timedelta(days=1)
    elif args.get("duration_days") is not None:
        end = start + timedelta(days=int(args["duration_days"]))
    if row.get("type") == "milestone":
        end = start
    if end < start:
        raise ToolError("end_date must not be before start_date.", ErrorCode.INVALID_INPUT)
    return start, end


@tool(
    name="update_schedule_task",
    title="Update schedule task",
    access="write",
    description="Change the name, dates, length or percent complete of a task on the project schedule.",
    details=(
        "Changes one task and returns it as the schedule shows it afterwards. start_date alone moves the task "
        "and keeps its length; end_date or duration_days change the length. Tasks that depend on it are not "
        "moved: check depends_on in list_schedule_tasks and move them too. The project's start and end dates "
        "follow the schedule. A schedule edit reaches nobody outside your company and one more call undoes "
        "it, so this tool runs without asking."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /projects/{project_id}/schedule-tasks/{task_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def update_schedule_task(ctx: ToolContext, args: dict[str, Any]) -> Any:
    project_id, task_id = args["project_id"], args["task_id"]
    changes = {"name", "start_date", "end_date", "duration_days", "percent_complete"} & {
        key for key, value in args.items() if value is not None
    }
    if not changes:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    body = await gantt(ctx, project_id)
    row = next((item for item in body.get("data") or [] if str(item.get("id")) == task_id), None)
    if row is None or str(row.get("project_id")) != project_id:
        raise ToolError(f"No task {task_id} on project {project_id}. Use list_schedule_tasks.", ErrorCode.TARGET_ERROR)
    start, end = new_dates(row, args)
    data = {key: value for key, value in row.items() if key not in _DROP}
    data.update(
        start_date=_stamp(start),
        end_date=_stamp(end),
        duration=(end - start).days,
        progress=round(number(args["percent_complete"]) / 100, 4)
        if args.get("percent_complete") is not None
        else number(row.get("progress")),
        open=bool(number(row.get("open"))),
    )
    if args.get("name"):
        data["text"] = text(args["name"])
    answer = await panel(
        ctx,
        "projects/update-schedule-tasks",
        {
            "project_id": project_id,
            "gantt_data": {"tasks": [{"entity": "task", "action": "update", "id": task_id, "data": data}], "count": 1},
        },
    )
    if (answer.get("data") or {}).get("error"):
        raise ToolError("Contractor Foreman did not save the schedule change.", ErrorCode.TARGET_ERROR)
    task = next(
        (item for item in task_rows(await gantt(ctx, project_id), project_id) if item["task_id"] == task_id), None
    )
    if task is None:
        raise ToolError("The task is no longer on the schedule.", ErrorCode.TARGET_ERROR)
    return {"project_id": project_id, "task": task}
