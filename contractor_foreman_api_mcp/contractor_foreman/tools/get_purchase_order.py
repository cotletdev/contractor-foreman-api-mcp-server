"""Get purchase order: one PO with its line items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import item_out, purchase_order_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "purchase_order_id": {"type": "integer", "description": "purchase_order_id from list_purchase_orders."}
    },
    "required": ["purchase_order_id"],
    "additionalProperties": False,
}

EXAMPLE_PO: dict[str, Any] = {
    "purchase_order_id": 881927,
    "number": "4",
    "subject": "Ceiling tiles and grid",
    "vendor_id": 6819139,
    "vendor": "Dana Whitfield (Triangle Lumber Supply)",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "order_date": "2026-10-21",
    "delivery_date": None,
    "total": 268.5,
    "status": "Draft",
    "ordered_by": "Michael Howard",
    "ship_via": None,
    "terms": None,
    "notes": None,
    "items": [
        {
            "item_id": 2502128,
            "description": "2x2 acoustic ceiling tiles, case of 16",
            "type": "material",
            "quantity": 3,
            "unit": "case",
            "unit_cost": 89.5,
            "total": 268.5,
            "cost_code": None,
        }
    ],
}


async def read_purchase_order(ctx: ToolContext, po_id: int) -> dict[str, Any]:
    row = first_record(await call(ctx, f"purchase-orders/{po_id}/detail"))
    if not row.get("purchase_order_id"):
        raise ToolError("Contractor Foreman did not find that purchase order.", ErrorCode.TARGET_ERROR)
    out = purchase_order_out(row, await date_format(ctx))
    items = await call(ctx, f"purchase-orders/{po_id}/get-items")
    data = items.get("data")
    found = data.get("items") if isinstance(data, dict) else data
    out["items"] = [item_out(i) for i in found or [] if isinstance(i, dict)]
    return out


@tool(
    name="get_purchase_order",
    title="Get purchase order",
    access="read",
    confirm=False,
    description="One purchase order with supplier, dates, status and its line items.",
    details=(
        "Reads one Contractor Foreman purchase order by purchase_order_id: what list_purchase_orders gives plus "
        "every line item with description, cost type, quantity, unit, unit cost, total and cost code."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /purchase-orders/{purchase_order_id}",
    example_response=EXAMPLE_PO,
)
async def get_purchase_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_purchase_order(ctx, args["purchase_order_id"])
