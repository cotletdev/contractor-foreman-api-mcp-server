"""Create purchase order: Purchase Orders, Add, then supplier and line items, as the panel saves one."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    call,
    created_id,
    my_user_id,
    status_id,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import ITEMS_SCHEMA, items_in
from contractor_foreman_api_mcp.contractor_foreman.tools.get_purchase_order import EXAMPLE_PO, read_purchase_order
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "subject": {"type": "string", "minLength": 1, "maxLength": 200},
        "vendor_id": {"type": "integer", "description": "The supplier's contact_id (list_contacts type vendor)."},
        "project_id": {"type": "integer", "description": "The project the order is for."},
        "order_date": {**DATE_SCHEMA, "description": "YYYY-MM-DD. Default: today."},
        "notes": {"type": "string", "maxLength": 2000},
        "items": ITEMS_SCHEMA,
    },
    "required": ["subject", "vendor_id", "items"],
    "additionalProperties": False,
}


@tool(
    name="create_purchase_order",
    title="Create purchase order",
    access="write",
    confirm=False,
    description="Creates a draft purchase order to a supplier with line items, optionally for a project.",
    details=(
        "Creates a Contractor Foreman purchase order in Draft status, ordered by the signed-in user: subject, "
        "supplier, project, order date, notes and line items (description, quantity, unit, unit cost, cost "
        "type). The supplier is not notified. Sending the PO stays a step in the app. Returns the saved order."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /purchase-orders",
    example_response=EXAMPLE_PO,
)
async def create_purchase_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    payload: dict[str, Any] = {
        "subject": args["subject"].strip(),
        "order_from": await my_user_id(ctx),
        "billing_status": await status_id(ctx, "purchase_order_billing_status", "po_on_hold"),
        "custom_purchase_orders_id": "",
        "access_to_custom_fields": 0,
    }
    if args.get("project_id"):
        payload["project_id"] = args["project_id"]
    created = await call(ctx, "purchase-orders/add", payload)
    po_id = created_id(created, "purchase_order_id")
    # The add form keeps today and takes no supplier or notes; the panel saves them as field edits.
    update: dict[str, Any] = {"supplier_id": args["vendor_id"]}
    if args.get("notes"):
        update["notes"] = args["notes"].strip()
    if args.get("order_date"):
        update["order_date"] = args["order_date"]
    await call(ctx, f"purchase-orders/{po_id}/update", update)
    await call(ctx, "purchase-orders/add-items", {"purchase_order_id": po_id, "items": items_in(args["items"])})
    return await read_purchase_order(ctx, po_id)
