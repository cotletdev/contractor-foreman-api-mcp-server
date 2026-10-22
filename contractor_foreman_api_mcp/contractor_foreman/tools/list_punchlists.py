"""List punchlists: the Punchlists list (`punchlists/get-list`, `start`/`limit`, filter by project)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import iso, number, panel, text
from contractor_foreman_api_mcp.core.helpers import limit
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "pattern": "^[0-9]+$", "description": "Only punchlists of this project."},
        "search": {"type": "string", "description": "Text to match, as the search box of the Punchlists list."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "punchlists": [
        {
            "punchlist_id": "72519",
            "number": 1,
            "name": "HVAC Punch",
            "project_name": "FAIRFIELD HOMES - Lot 14 HVAC System",
            "customer": "John Pence (Fairfield Homes)",
            "status": "Open",
            "open_items": 2,
            "completed_items": 0,
            "assignees": ["Rick Jones (A-Quality Heating and Air Conditioning)"],
            "created_date": "2026-10-20",
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_punchlists",
    title="List punchlists",
    access="read",
    description="Punchlists with project, status, open and completed item counts and who the items are assigned to.",
    details=(
        "Returns punchlists, optionally for one project, with the number of open and completed items and "
        "the people their items are assigned to. status is the one the Punchlists list shows. Pages hold up to 100 "
        "punchlists; pass next_cursor back as cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /punchlists",
    example_response=EXAMPLE_RESPONSE,
)
async def list_punchlists(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 30, 100)
    cursor = args.get("cursor")
    start = int(cursor) if cursor and cursor.isdigit() else 0
    payload: dict[str, Any] = {"limit": size, "start": start, "ignore_filter": 1}
    if args.get("project_id"):
        payload["filter"] = {"project": args["project_id"]}
    if args.get("search"):
        payload["search"] = args["search"]
    body = await panel(ctx, "punchlists/get-list", payload)
    rows = (body.get("data") or {}).get("punchlist") or []
    lists = [
        {
            "punchlist_id": str(row.get("punchlist_id")),
            "number": row.get("company_punchlist_id"),
            "name": text(row.get("punchlist_name")),
            "project_name": text(row.get("project_name")),
            "customer": text(row.get("customer_name")),
            "status": text(row.get("punchlist_status")),
            "open_items": int(number(row.get("incomplete_items"))),
            "completed_items": int(number(row.get("completed_items"))),
            "assignees": [
                text(user.get("assignee_name")) for user in row.get("assignes_to") or [] if user.get("assignee_name")
            ],
            "created_date": iso(row.get("date_added")),
        }
        for row in rows
    ]
    return {"punchlists": lists, "next_cursor": str(start + size) if len(rows) == size else None}
