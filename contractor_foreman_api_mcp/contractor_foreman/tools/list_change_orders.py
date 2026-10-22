"""List change orders: change orders and change order requests, newest first, with status and total."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._change_orders import STATUS_NAMES, row_out, status_id
from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import call
from contractor_foreman_api_mcp.core.helpers import limit, page_cursor
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "description": "Only this project's (list_projects)."},
        "kind": {
            "type": "string",
            "enum": ["change_order", "request", "all"],
            "default": "all",
            "description": "request = change order requests (COR) not yet turned into a change order.",
        },
        "status": {
            "type": "string",
            "enum": STATUS_NAMES,
            "description": "With kind all or change_order, a change order status. Request statuses need kind request.",
        },
        "search": {"type": "string", "description": "Matches the title or number."},
        "include_archived": {"type": "boolean", "default": False},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "change_orders": [
        {
            "change_order_id": "540713",
            "number": "235236",
            "title": "Add under-cabinet lighting",
            "kind": "change_order",
            "status": "open",
            "status_name": "Open",
            "project_id": "1678167",
            "project_name": "Kitchen Upgrade",
            "customer_name": "Dana Whitfield (Whitfield Homes)",
            "date": "2026-10-21",
            "total": 680.4,
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_change_orders",
    title="List change orders",
    access="read",
    description="Change orders and change order requests, newest first, with status, project and total.",
    details=(
        "The Change Orders list: number, title, kind (change_order or request), status, project, customer, "
        "date and total in dollars. Filter by project, kind, status or a search over title and number. "
        "Archived ones only with include_archived. Change orders have the statuses open, pending_approval, "
        "on_hold, approved, denied, billed. Requests have draft, on_hold, approved, denied, closed. A status "
        "that does not fit the kind stops the call. get_change_order gives the line items."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /change-orders",
    example_response=EXAMPLE_RESPONSE,
)
async def list_change_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 25, 100)
    page = page_cursor(args.get("cursor"))
    kind = {"change_order": "co", "request": "cor"}.get(args.get("kind", "all"))
    filters: dict[str, Any] = {"status": "" if args.get("include_archived") else "0"}
    if args.get("project_id"):
        filters["project"] = str(args["project_id"])
    if kind:
        filters["type"] = kind
    if args.get("status"):
        filters["billing_status"] = status_id(kind or "co", args["status"])
    payload: dict[str, Any] = {"page": page - 1, "limit": size, "ignore_filter": 1, "filter": filters}
    if kind:
        payload["type"] = kind
    if args.get("search"):
        payload["search"] = args["search"]
    rows = ((await call(ctx, "change-orders/get-list", payload)).get("data") or {}).get("changeOrders") or []
    return {
        "change_orders": [row_out(row) for row in rows],
        "next_cursor": str(page + 1) if len(rows) == size else None,
    }
