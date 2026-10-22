"""Add change order items: appends priced line items to a change order or request."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._change_orders import add_items, detail
from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import LINE_ITEM, dollars
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "change_order_id": {"type": "string", "minLength": 1, "description": "From list_change_orders."},
        "items": {"type": "array", "minItems": 1, "maxItems": 100, "items": LINE_ITEM},
    },
    "required": ["change_order_id", "items"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "change_order_id": "540713",
    "added": [
        {
            "item_id": "1810376",
            "name": "Electrician labor",
            "type": "labor",
            "quantity": 4,
            "unit": "Hrs",
            "unit_cost": 75.0,
            "markup_percent": 20.0,
            "total": 360.0,
            "cost_code": None,
            "description": None,
            "section": None,
        }
    ],
    "total": 680.4,
}


@tool(
    name="add_change_order_items",
    title="Add change order items",
    access="write",
    description="Adds priced line items to a change order or change order request.",
    details=(
        "Adds line items at the end of the change order's first section: name, type (material, labor, "
        "equipment, subcontractor, other), quantity, unit, unit cost in dollars and markup percent. The app "
        "computes totals. Returns the saved items and the new total."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /change-orders/{change_order_id}/items",
    example_response=EXAMPLE_RESPONSE,
)
async def add_change_order_items(ctx: ToolContext, args: dict[str, Any]) -> Any:
    change_order_id = str(args["change_order_id"])
    await detail(ctx, change_order_id)
    added = await add_items(ctx, change_order_id, args["items"])
    data = await detail(ctx, change_order_id)
    return {"change_order_id": change_order_id, "added": added, "total": dollars(data.get("total")) or 0.0}
