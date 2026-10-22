"""Get clock status: who is clocked in now, and this week's hours (Time Cards dashboard)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, num, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_timecards import hours
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "me_clocked_in": False,
    "my_running_timecard_id": None,
    "clocked_in": [
        {
            "employee": "Luis Ramirez",
            "project": "Speedway - Tenant Fit Out",
            "clock_in": "07:02 AM",
            "timecard_id": 13199501,
        }
    ],
    "week": {"regular_hours": 0.0, "overtime_hours": 0.0, "total_hours": 0.0},
    "my_week": {"regular_hours": 0.0, "overtime_hours": 0.0, "total_hours": 0.0},
    "previous_week": {"regular_hours": 0.0, "overtime_hours": 0.0, "total_hours": 0.0},
}


def _week(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "regular_hours": hours(block.get("regular_hours")) or 0.0,
        "overtime_hours": hours(block.get("ot_hours")) or 0.0,
        "total_hours": hours(block.get("total_hours")) or 0.0,
    }


@tool(
    name="get_clock_status",
    title="Get clock status",
    access="read",
    confirm=False,
    description="Who is clocked in right now, whether you are, and this and last week's crew hours.",
    details=(
        "Reads the Contractor Foreman Time Cards dashboard: the employees clocked in at this moment with their "
        "project and clock-in time, whether the signed-in user is clocked in (and that card's id), and the "
        "regular, overtime and total hours of the whole team and of the signed-in user for this week and last."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /clock-status",
    example_response=EXAMPLE_RESPONSE,
)
async def get_clock_status(ctx: ToolContext, args: dict[str, Any]) -> Any:
    dash = await call(ctx, "time-card/dashboard", {"period": "last_vs_this", "ignore_filter": 1})
    mine = await call(ctx, "time-card/get-timecard-current-status")
    hours_data = ((dash.get("data") or {}).get("reference_data") or {}).get("working_hours") or {}
    running = num((mine.get("data") or {}).get("current_timecard"))
    clocked = [
        {
            "employee": text(row.get("employee") or row.get("emp_name") or row.get("display_name")),
            "project": text(row.get("project_name")),
            "clock_in": text(row.get("clock_in_time") or row.get("clock_in")),
            "timecard_id": num(row.get("timecard_id")),
        }
        for row in hours_data.get("clock_in_timecard") or []
        if isinstance(row, dict)
    ]
    return {
        "me_clocked_in": running is not None,
        "my_running_timecard_id": running,
        "clocked_in": clocked,
        "week": _week(hours_data.get("current_week") or {}),
        "my_week": _week(hours_data.get("current_week_me") or {}),
        "previous_week": _week(hours_data.get("previous_week") or {}),
    }
