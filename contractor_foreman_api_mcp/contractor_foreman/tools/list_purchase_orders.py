"""List purchase orders: Purchase Orders sent to suppliers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import (
    LIST_PROPS,
    list_records,
    purchase_order_out,
)
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {**LIST_PROPS, "limit": LIMIT_SCHEMA, "cursor": CURSOR_SCHEMA},
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_ROW: dict[str, Any] = {
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
}


@tool(
    name="list_purchase_orders",
    title="List purchase orders",
    access="read",
    confirm=False,
    description="Purchase orders with supplier, project, order date, total and status.",
    details=(
        "Reads the Contractor Foreman Purchase Orders list, newest first: PO number, subject, supplier, "
        "project, order and delivery date, total, status (Draft, Submitted, Approved, Received, Closed ...) "
        "and who ordered it. Filter by project or search. get_purchase_order adds the line items."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /purchase-orders",
    example_response={"purchase_orders": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_purchase_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "purchase-orders/get-list", None, purchase_order_out)
    return {"purchase_orders": found, "next_cursor": cursor}
