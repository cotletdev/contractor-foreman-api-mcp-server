"""List projects: the Projects list of the panel, in its order, a page at a time."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import iso, money, number, panel, text
from contractor_foreman_api_mcp.core.helpers import limit, page_cursor
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# Project status keys of the panel ("Open" tab = everything but completed), global types 21.10.2026.
STATUSES = ["pending", "unscheduled", "project_submittal", "bidding", "started", "completed"]
_OPEN = "bidding,project_submittal,started,unscheduled,pending"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "search": {"type": "string", "description": "Match on project name, number or customer."},
        "status": {"type": "string", "enum": STATUSES, "description": "Only projects in this stage."},
        "include_completed": {
            "type": "boolean",
            "default": False,
            "description": "Include completed projects. Ignored when status is set.",
        },
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "projects": [
        {
            "project_id": "1678216",
            "number": "HR-1001",
            "name": "Kitchen remodel - Oak St",
            "customer": "John Pence (Fairfield Homes)",
            "status": "started",
            "status_name": "Started",
            "type": "Residential",
            "start_date": "2026-10-26",
            "end_date": "2026-12-18",
            "contract_amount": 48500.0,
            "budgeted_cost": 36200.0,
            "committed_cost": 12400.0,
            "actual_cost": 8100.0,
            "invoiced": 15000.0,
            "paid": 10000.0,
            "percent_complete": 39.0,
        }
    ],
    "next_cursor": None,
}


def project_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": str(row.get("id")),
        "number": text(row.get("project_id")),
        "name": text(row.get("project_name")),
        "customer": text(row.get("customer_name")),
        "status": row.get("project_status_key") or row.get("project_status"),
        "status_name": text(row.get("project_status_name")),
        "type": text(row.get("project_type_name")),
        "start_date": iso(row.get("start_date")),
        "end_date": iso(row.get("end_date")),
        "contract_amount": money(row.get("no_tax_contract_amount")),
        "budgeted_cost": money(row.get("budgeted")),
        "committed_cost": money(row.get("commited")),
        "actual_cost": money(row.get("actual")),
        "invoiced": money(row.get("invoiced")),
        "paid": money(row.get("paid_amount")),
        "percent_complete": round(number(row.get("progress")) * 100, 1),
    }


@tool(
    name="list_projects",
    title="List projects",
    access="read",
    description="Projects with customer, stage, dates, contract amount, costs and percent complete.",
    details=(
        "Returns active (not archived) projects in the order of the Projects list. Completed projects are "
        "left out unless include_completed is true or status asks for them. search matches the project name, "
        "number or customer. Amounts are in the account's currency: contract amount without tax, budgeted, "
        "committed and actual cost, invoiced and paid. Pages hold up to 100 projects; pass next_cursor back "
        "as cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects",
    example_response=EXAMPLE_RESPONSE,
)
async def list_projects(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page = page_cursor(args.get("cursor"))
    size = limit(args, 25, 100)
    project_filter: dict[str, Any] = {"status": "0", "tab": "all"}
    if args.get("status"):
        project_filter["project_status"] = args["status"]
    elif not args.get("include_completed"):
        project_filter.update(tab="open", project_status=_OPEN)
    payload: dict[str, Any] = {"filter": project_filter, "limit": size, "page": page - 1}
    if args.get("search"):
        payload["search"] = args["search"]
    body = await panel(ctx, "projects/get-project-list", payload)
    rows = (body.get("data") or {}).get("data") or []
    return {
        "projects": [project_row(row) for row in rows],
        "next_cursor": str(page + 1) if len(rows) == size else None,
    }
