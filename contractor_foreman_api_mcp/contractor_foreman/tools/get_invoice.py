"""Get invoice: one invoice with customer, terms, line items and payments."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import call, dollars, item_out, plain
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import detail, payments, row_out
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"invoice_id": {"type": "string", "minLength": 1, "description": "From list_invoices."}},
    "required": ["invoice_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "invoice_id": "2049756",
    "number": "10",
    "status": "submitted",
    "status_name": "Submitted",
    "project_id": "1678167",
    "project_name": "Kitchen Upgrade",
    "customer_id": "6819060",
    "customer_name": "Dana Whitfield (Whitfield Homes)",
    "invoice_date": "2026-10-21",
    "due_date": "2026-11-20",
    "total": 1500.0,
    "balance_due": 1000.0,
    "overdue": False,
    "customer_email": "dana@example.com",
    "terms": "Net 30",
    "retainage_percent": 0.0,
    "paid": 500.0,
    "description": None,
    "items": [
        {
            "item_id": "10930638",
            "name": "Pantry cabinet installation, progress billing",
            "type": "other",
            "quantity": 1,
            "unit": "ls",
            "unit_cost": 1500.0,
            "markup_percent": None,
            "total": 1500.0,
            "cost_code": None,
            "description": None,
            "section": None,
        }
    ],
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
        }
    ],
}


@tool(
    name="get_invoice",
    title="Get invoice",
    access="read",
    description="One invoice with customer, dates, terms, line items, payments and balance due.",
    details=(
        "Everything on one invoice: status, project, customer and their email, invoice and due dates, terms, "
        "retainage, total, amount paid and balance due in dollars, the line items and every payment recorded "
        "against it (date, amount, method, status)."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /invoices/{invoice_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    invoice_id = str(args["invoice_id"])
    data = await detail(ctx, invoice_id)
    items = (await call(ctx, f"invoices/{int(invoice_id)}/get-invoice-items", {"data_for": "all"})).get("data") or {}
    customer = data.get("customer") or {}
    return {
        **row_out(data),
        "customer_email": plain(data.get("customer_email") or customer.get("email")),
        "terms": plain(data.get("term_name")),
        "retainage_percent": float(data.get("invoice_retainage") or 0),
        "paid": dollars(data.get("payment_amount")) or 0.0,
        "description": plain(data.get("description")),
        "items": [item_out(row) for row in items.get("items") or []],
        "payments": await payments(ctx, invoice_id),
    }
