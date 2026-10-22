"""Get time card: one card with its entries per employee and cost code."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record, num, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_timecards import (
    EXAMPLE_TIMECARD,
    hours,
    minutes_to_hours,
    timecard_out,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"timecard_id": {"type": "integer", "description": "timecard_id from list_time_cards."}},
    "required": ["timecard_id"],
    "additionalProperties": False,
}


@tool(
    name="get_time_card",
    title="Get time card",
    access="read",
    confirm=False,
    description="One time card or crew sheet with hours per employee and cost code.",
    details=(
        "Reads one Contractor Foreman time card by timecard_id: what list_time_cards gives plus one entry per "
        "employee and cost code with the hours worked and the entry's notes. A crew sheet lists every crew member."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /time-cards/{timecard_id}",
    example_response={
        **EXAMPLE_TIMECARD,
        "entries": [
            {
                "employee_id": 6819056,
                "employee": "Michael Howard",
                "cost_code": "Project Management/Coordination",
                "hours": 20.0,
                "notes": None,
            }
        ],
    },
)
async def get_time_card(ctx: ToolContext, args: dict[str, Any]) -> Any:
    row = first_record(await call(ctx, f"time-card/{args['timecard_id']}/get-timecard-detail"))
    if not row.get("timecard_id"):
        raise ToolError("Contractor Foreman did not find that time card.", ErrorCode.TARGET_ERROR)
    out = timecard_out(row, await date_format(ctx))
    out["entries"] = [
        {
            "employee_id": num(item.get("user_id")),
            "employee": text(
                item.get("crew_emp") or " ".join(p for p in (item.get("first_name"), item.get("last_name")) if p)
            ),
            "cost_code": text(item.get("cost_code_name")),
            "hours": hours(item.get("hours_worked"))
            if ":" in str(item.get("hours_worked") or "")
            else minutes_to_hours(item.get("work_mins")),
            "notes": text(item.get("notes")),
        }
        for item in row.get("items") or []
        if isinstance(item, dict)
    ]
    return out
