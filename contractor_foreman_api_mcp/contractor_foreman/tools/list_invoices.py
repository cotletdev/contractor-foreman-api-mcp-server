"""List invoices: newest first, with balance due and whether each is overdue."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import INVOICE_STATUSES, call
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import row_out
from contractor_foreman_api_mcp.core.helpers import limit, page_cursor
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "description": "Only this project's (list_projects)."},
        "customer_id": {"type": "string", "description": "Only this customer's."},
        "status": {"type": "string", "enum": list(INVOICE_STATUSES)},
        "unpaid_only": {
            "type": "boolean",
            "default": False,
            "description": "Only submitted or on-hold invoices with a balance due.",
        },
        "due_before": {"type": "string", "format": "date", "description": "Only invoices due before this date."},
        "search": {"type": "string", "description": "Matches the number, project or customer."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "invoices": [
        {
            "invoice_id": "2049701",
            "number": "4",
            "status": "submitted",
            "status_name": "Submitted",
            "project_id": "1678164",
            "project_name": "Speedway - Tenant Fit Out",
            "customer_id": "6819089",
            "customer_name": "Jacob Carver (Carver & Co.)",
            "invoice_date": "2026-09-15",
            "due_date": "2026-10-15",
            "total": 13094.3,
            "balance_due": 8594.3,
            "overdue": True,
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_invoices",
    title="List invoices",
    access="read",
    description="Invoices, newest first, with status, totals, balance due and an overdue flag.",
    details=(
        "The Invoices list: number, status (draft, submitted, on_hold, paid, denied, write_off), project, "
        "customer, invoice and due dates, total and balance due in dollars, and overdue (past the due date "
        "with a balance). Archived invoices are left out. unpaid_only keeps submitted and on-hold invoices "
        "that still have a balance. status, when given, replaces the unpaid_only status filter. unpaid_only "
        "and due_before filter the page you get, so a page can hold fewer than limit. Keep the cursor going "
        "until next_cursor is null. get_invoice gives the items and payments."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /invoices",
    example_response=EXAMPLE_RESPONSE,
)
async def list_invoices(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 25, 100)
    page = page_cursor(args.get("cursor"))
    filters: dict[str, Any] = {"status": "0"}
    if args.get("project_id"):
        filters["project"] = str(args["project_id"])
    if args.get("customer_id"):
        filters["customer"] = str(args["customer_id"])
    if args.get("unpaid_only"):
        filters["billing_status"] = f"{INVOICE_STATUSES['submitted']},{INVOICE_STATUSES['on_hold']}"
    if args.get("status"):
        filters["billing_status"] = str(INVOICE_STATUSES[args["status"]])
    payload: dict[str, Any] = {"page": page - 1, "length": size, "ignore_filter": 1, "filter": filters}
    if args.get("search"):
        payload["search"] = args["search"]
    rows = (await call(ctx, "invoices", payload)).get("data") or []
    invoices = [row_out(row) for row in rows]
    if args.get("unpaid_only"):
        invoices = [row for row in invoices if row["balance_due"] > 0]
    if before := args.get("due_before"):
        invoices = [row for row in invoices if row["due_date"] and row["due_date"] < before]
    return {"invoices": invoices, "next_cursor": str(page + 1) if len(rows) == size else None}
