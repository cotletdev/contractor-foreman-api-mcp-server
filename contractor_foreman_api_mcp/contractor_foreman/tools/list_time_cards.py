"""List time cards: Time Cards, the list of clock-ins with hours per card."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    CURSOR_SCHEMA,
    DATE_SCHEMA,
    LIMIT_SCHEMA,
    call,
    date_format,
    next_cursor,
    page,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_timecards import EXAMPLE_TIMECARD, timecard_out
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "start_date": {**DATE_SCHEMA, "description": "Cards from this day on, YYYY-MM-DD."},
        "end_date": {**DATE_SCHEMA, "description": "Cards up to this day, YYYY-MM-DD."},
        "project_id": {"type": "integer", "description": "Only this project's cards."},
        "employee_id": {"type": "integer", "description": "Only this employee's cards (contact_id)."},
        "limit": LIMIT_SCHEMA,
        "cursor": CURSOR_SCHEMA,
    },
    "required": [],
    "additionalProperties": False,
}


@tool(
    name="list_time_cards",
    title="List time cards",
    access="read",
    confirm=False,
    description="Time cards with employee or crew, project, clock-in and clock-out times and hours, newest first.",
    details=(
        "Reads the Contractor Foreman Time Cards list, newest first: employee cards and crew sheets with the "
        "project, day, clock-in and clock-out time, hours worked and break hours. A card still running has "
        "running true and no hours yet. Filter by a date range, a project or an employee. get_time_card gives "
        "one card's entries per person and cost code."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /time-cards",
    example_response={"time_cards": [EXAMPLE_TIMECARD], "next_cursor": None},
)
async def list_time_cards(ctx: ToolContext, args: dict[str, Any]) -> Any:
    start, size = page(args)
    flt: dict[str, Any] = {}
    for key, field in (("start_date", "start_date"), ("end_date", "end_date")):
        if args.get(key):
            flt[field] = args[key]
    if args.get("project_id"):
        flt["project"] = str(args["project_id"])
    if args.get("employee_id"):
        flt["directory"] = str(args["employee_id"])
    payload: dict[str, Any] = {"page": start // size, "length": size}
    if flt:
        payload["filter"] = flt
    body = await call(ctx, "time-card/get-timecards-list", payload)
    found = [r for r in body.get("data") or [] if isinstance(r, dict)]
    fmt = await date_format(ctx)
    return {"time_cards": [timecard_out(r, fmt) for r in found], "next_cursor": next_cursor(start, size, len(found))}
