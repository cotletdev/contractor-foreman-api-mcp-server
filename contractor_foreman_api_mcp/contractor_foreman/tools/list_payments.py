"""List payments: payments received on invoices, newest first (payment/get-payments-list)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import call, plain
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import payment_out
from contractor_foreman_api_mcp.core.helpers import limit, page_cursor
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "description": "Only this project's (list_projects)."},
        "customer_id": {"type": "string", "description": "Only this customer's."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "payments": [
        {
            "payment_id": "3621588",
            "date": "2026-10-21",
            "amount": 500.0,
            "method": "check",
            "status": "received",
            "notes": "Check 1042, deposit",
            "invoice_id": "2049756",
            "invoice_number": "10",
            "customer_name": "Dana Whitfield (Whitfield Homes)",
            "project_name": "Kitchen Upgrade",
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_payments",
    title="List payments",
    access="read",
    description="Payments received on invoices, newest first, with amount, method and invoice.",
    details=(
        "The Payments list: date, amount in dollars, method, status (received, in_review, verified, failed), "
        "notes, the invoice it pays, customer and project. get_invoice shows the payments of one invoice."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /payments",
    example_response=EXAMPLE_RESPONSE,
)
async def list_payments(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 25, 100)
    page = page_cursor(args.get("cursor"))
    filters: dict[str, Any] = {"status": "0"}
    if args.get("project_id"):
        filters["project"] = str(args["project_id"])
    if args.get("customer_id"):
        filters["customer"] = str(args["customer_id"])
    payload = {"start": (page - 1) * size, "limit": size, "ignore_filter": 1, "filter": filters}
    rows = (await call(ctx, "payment/get-payments-list", payload)).get("data") or []
    return {
        "payments": [
            {
                **payment_out(row),
                "customer_name": plain(row.get("customer_name")),
                "project_name": row.get("project_name"),
            }
            for row in rows
        ],
        "next_cursor": str(page + 1) if len(rows) == size else None,
    }
