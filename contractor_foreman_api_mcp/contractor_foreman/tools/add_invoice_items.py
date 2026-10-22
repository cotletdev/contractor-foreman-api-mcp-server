"""Add invoice items: appends priced line items to an invoice."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import LINE_ITEM, dollars
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import add_items, detail
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_id": {"type": "string", "minLength": 1, "description": "From list_invoices or create_invoice."},
        "items": {"type": "array", "minItems": 1, "maxItems": 100, "items": LINE_ITEM},
    },
    "required": ["invoice_id", "items"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "invoice_id": "2049756",
    "added": [
        {
            "item_id": "10930640",
            "name": "Extra outlet, pantry wall",
            "type": "other",
            "quantity": 1,
            "unit": "ea",
            "unit_cost": 185.0,
            "markup_percent": None,
            "total": 185.0,
            "cost_code": None,
            "description": None,
            "section": None,
        }
    ],
    "total": 1685.0,
    "balance_due": 1185.0,
}


@tool(
    name="add_invoice_items",
    title="Add invoice items",
    access="write",
    description="Adds priced line items to an invoice.",
    details=(
        "Adds plain priced lines at the end of an invoice: name, type, quantity, unit, unit cost in dollars, "
        "markup percent. Items billed from an estimate, change order or schedule of values are added in the "
        "app. Returns the saved items, the new total and the balance due."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /invoices/{invoice_id}/items",
    example_response=EXAMPLE_RESPONSE,
)
async def add_invoice_items(ctx: ToolContext, args: dict[str, Any]) -> Any:
    invoice_id = str(args["invoice_id"])
    await detail(ctx, invoice_id)
    added = await add_items(ctx, invoice_id, args["items"])
    data = await detail(ctx, invoice_id)
    return {
        "invoice_id": invoice_id,
        "added": added,
        "total": dollars(data.get("total")) or 0.0,
        "balance_due": dollars(data.get("due_balance")) or 0.0,
    }
