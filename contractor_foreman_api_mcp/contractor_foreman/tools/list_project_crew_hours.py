"""List project crew hours: a project's Time Cards tab, summed per employee."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    call,
    date_format,
    iso,
    num,
    text,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_timecards import minutes_to_hours
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "integer", "description": "The project's numeric id (list_projects)."},
        "start_date": {**DATE_SCHEMA, "description": "Hours from this day on, YYYY-MM-DD."},
        "end_date": {**DATE_SCHEMA, "description": "Hours up to this day, YYYY-MM-DD."},
    },
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "project_id": 1678164,
    "total_hours": 52.0,
    "total_cost": 616.48,
    "employees": [
        {"employee": "Michael Howard", "hours": 36.0, "overtime_hours": 0.0, "cost": 0.0, "days": 3},
        {"employee": "Martin Scovill", "hours": 16.0, "overtime_hours": 0.0, "cost": 616.48, "days": 2},
    ],
    "entries": [
        {
            "date": "2024-01-31",
            "employee": "Michael Howard",
            "cost_code": None,
            "hours": 20.0,
            "overtime_hours": 0.0,
            "cost": 0.0,
            "timecard_id": 13199473,
        }
    ],
}


def _dollars(value: Any) -> float:
    """get-timecards gives total_cost in dollars, unlike the cents elsewhere (wage is cents)."""
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


@tool(
    name="list_project_crew_hours",
    title="List project crew hours",
    access="read",
    confirm=False,
    description="Hours and labor cost logged on one project, per employee and per day and cost code.",
    details=(
        "Reads the time logged on a Contractor Foreman project (the project's Time Cards tab): every entry with the "
        "day, employee, cost code, regular and overtime hours and labor cost, plus a sum per employee (most hours "
        "first) and the project total. days counts the distinct days an employee logged. Cost uses the wages in the "
        "Directory and is 0 when no wage is set. Optional date range."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/{project_id}/crew-hours",
    example_response=EXAMPLE_RESPONSE,
)
async def list_project_crew_hours(ctx: ToolContext, args: dict[str, Any]) -> Any:
    body = await call(ctx, f"projects/{args['project_id']}/get-timecards")
    fmt = await date_format(ctx)
    since, until = args.get("start_date"), args.get("end_date")
    entries: list[dict[str, Any]] = []
    for row in body.get("data") or []:
        if not isinstance(row, dict):
            continue
        day = iso(row.get("record_date"), fmt)
        if (since and (not day or day < since)) or (until and (not day or day > until)):
            continue
        entries.append(
            {
                "date": day,
                "employee": text(row.get("employee")),
                "cost_code": text(row.get("cost_code_name")),
                "hours": minutes_to_hours(row.get("work_mins")),
                "overtime_hours": minutes_to_hours(row.get("ot_hours")),
                "cost": _dollars(row.get("total_cost")),
                "timecard_id": num(row.get("timecard_id")),
            }
        )
    people: dict[str, dict[str, Any]] = {}
    for entry in entries:
        name = entry["employee"] or "Unknown"
        person = people.setdefault(
            name, {"employee": name, "hours": 0.0, "overtime_hours": 0.0, "cost": 0.0, "days": set()}
        )
        person["hours"] += entry["hours"]
        person["overtime_hours"] += entry["overtime_hours"]
        person["cost"] += entry["cost"]
        person["days"].add(entry["date"])
    employees = [
        {
            **p,
            "hours": round(p["hours"], 2),
            "overtime_hours": round(p["overtime_hours"], 2),
            "cost": round(p["cost"], 2),
            "days": len(p["days"]),
        }
        for p in sorted(people.values(), key=lambda p: -p["hours"])
    ]
    return {
        "project_id": args["project_id"],
        "total_hours": round(sum(e["hours"] for e in entries), 2),
        "total_cost": round(sum(e["cost"] for e in entries), 2),
        "employees": employees,
        "entries": entries,
    }
