"""List RFIs: RFI & Notices, the requests for information."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    CURSOR_SCHEMA,
    LIMIT_SCHEMA,
    call,
    date_format,
    next_cursor,
    page,
    rows,
    statuses,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import RFI_TYPE, rfi_out
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import LIST_PROPS
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {**LIST_PROPS, "limit": LIMIT_SCHEMA, "cursor": CURSOR_SCHEMA},
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RFI: dict[str, Any] = {
    "rfi_id": 238990,
    "number": "3",
    "title": "Confirm grease trap location",
    "question": "Plans show the grease trap under the prep sink, but it conflicts with the floor drain.",
    "reference_area": None,
    "plan_sheet": None,
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "date": "2026-10-21",
    "response_needed_by": "2026-10-24",
    "response_received": None,
    "answer": None,
    "status": "Draft",
}


@tool(
    name="list_rfis",
    title="List RFIs",
    access="read",
    confirm=False,
    description="Requests for information with question, project, dates, answer and status.",
    details=(
        "Reads the RFIs in Contractor Foreman's RFI & Notices module, newest first: number, title, the question, "
        "area and plan sheet it refers to, project, date, response needed by, response received, the answer and "
        "status (Draft, Submitted, Outstanding, Received, Closed). Schedule and compliance notices from the same "
        "module are left out, so a page can hold fewer than limit. Filter by project or search."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /rfis",
    example_response={"rfis": [EXAMPLE_RFI], "next_cursor": None},
)
async def list_rfis(ctx: ToolContext, args: dict[str, Any]) -> Any:
    start, size = page(args)
    payload: dict[str, Any] = {"start": start, "limit": size, "ignore_filter": 1}
    if args.get("project_id"):
        payload["filter"] = {"project": str(args["project_id"])}
    if args.get("search"):
        payload["search"] = args["search"].strip()
    found = [r for r in rows(await call(ctx, "rfi", payload), "correspondenceData") if isinstance(r, dict)]
    fmt = await date_format(ctx)
    names = {r["id"]: r["name"] for r in await statuses(ctx, "correspondence_rfi")}
    return {
        "rfis": [rfi_out(r, fmt, names) for r in found if r.get("type") == RFI_TYPE],
        "next_cursor": next_cursor(start, size, len(found)),
    }
