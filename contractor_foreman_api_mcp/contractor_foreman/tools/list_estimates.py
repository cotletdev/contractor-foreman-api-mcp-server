"""List estimates: the Estimates page list, newest first, with project, status, customer and totals."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    ESTIMATE_STATUSES,
    call,
    dollars,
    iso,
    key_of,
    number,
    plain,
)
from contractor_foreman_api_mcp.core.helpers import limit, page_cursor
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "description": "Only estimates of this project (list_projects)."},
        "status": {"type": "string", "enum": list(ESTIMATE_STATUSES)},
        "search": {"type": "string", "description": "Matches the title, number or customer."},
        "include_archived": {"type": "boolean", "default": False},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "estimates": [
        {
            "estimate_id": "1616575",
            "number": "5",
            "title": "Pantry Cabinet Addition",
            "status": "estimating",
            "status_name": "Estimating",
            "project_id": "1678167",
            "project_name": "Kitchen Upgrade",
            "customer_id": "6819060",
            "customer_name": "Dana Whitfield (Whitfield Homes)",
            "estimate_date": "2026-10-21",
            "expire_date": "2026-11-20",
            "total": 1338.0,
            "archived": False,
        }
    ],
    "next_cursor": None,
}


def estimate_row(row: dict[str, Any]) -> dict[str, Any]:
    status = row.get("approval_type_key") or row.get("approval_type")
    return {
        "estimate_id": str(row.get("estimate_id")),
        "number": row.get("company_estimate_id"),
        "title": row.get("title"),
        "status": key_of(ESTIMATE_STATUSES, status),
        "status_name": row.get("approval_type_name"),
        "project_id": str(row["project_id"]) if number(row.get("project_id")) else None,
        "project_name": row.get("project_name"),
        "customer_id": str(row["customer_id"]) if number(row.get("customer_id")) else None,
        "customer_name": plain(row.get("customer_name")),
        "estimate_date": iso(row.get("estimate_date")),
        "expire_date": iso(row.get("expire_date")),
        "total": dollars(row.get("total")),
        "archived": row.get("is_deleted") == 1,
    }


@tool(
    name="list_estimates",
    title="List estimates",
    access="read",
    description="Estimates, newest first, with status, project, customer and total.",
    details=(
        "The Estimates list: number, title, status, project, customer, dates and total in dollars. Filter by "
        "project, status or a search over title, number and customer. Archived estimates only with "
        "include_archived. "
        "get_estimate gives the line items."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /estimates",
    example_response=EXAMPLE_RESPONSE,
)
async def list_estimates(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 25, 100)
    page = page_cursor(args.get("cursor"))
    filters: dict[str, Any] = {"status": "" if args.get("include_archived") else "0"}
    if args.get("project_id"):
        filters["project"] = str(args["project_id"])
    if args.get("status"):
        filters["approval_type"] = ESTIMATE_STATUSES[args["status"]]
    payload: dict[str, Any] = {"start": (page - 1) * size, "limit": size, "ignore_filter": 1, "filter": filters}
    if args.get("search"):
        payload["search"] = args["search"]
    rows = ((await call(ctx, "estimate/get-list", payload)).get("data") or {}).get("estimates") or []
    return {
        "estimates": [estimate_row(row) for row in rows],
        "next_cursor": str(page + 1) if len(rows) == size else None,
    }
