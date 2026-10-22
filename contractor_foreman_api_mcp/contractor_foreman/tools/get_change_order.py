"""Get change order: one change order or request with its description and line items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._change_orders import detail, full_out, sections
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"change_order_id": {"type": "string", "minLength": 1, "description": "From list_change_orders."}},
    "required": ["change_order_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
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
    "description": "Client request on 20 Oct: add LED lighting under the new upper cabinets.",
    "customer_id": "6819060",
    "estimate_id": None,
    "time_delay_days": None,
    "items": [
        {
            "item_id": "1810375",
            "name": "LED under-cabinet light kit",
            "type": "material",
            "quantity": 3,
            "unit": "ea",
            "unit_cost": 89.0,
            "markup_percent": 20.0,
            "total": 320.4,
            "cost_code": None,
            "description": None,
            "section": "Item",
        }
    ],
    "sections": [{"section_id": "538997", "name": "Item"}],
}


@tool(
    name="get_change_order",
    title="Get change order",
    access="read",
    description="One change order or request with description, status, total and line items.",
    details=(
        "Everything on one change order or change order request: number, title, status, project, customer, "
        "date, the reason (description), the estimate it came from, time delay and the priced line items."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /change-orders/{change_order_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_change_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    change_order_id = str(args["change_order_id"])
    data = await detail(ctx, change_order_id)
    return full_out(data, await sections(ctx, change_order_id))
