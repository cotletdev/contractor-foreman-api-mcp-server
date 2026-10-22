"""Delete change order: removes one change order or request (common/service delete_module_record)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._change_orders import detail
from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import service
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"change_order_id": {"type": "string", "minLength": 1, "description": "From list_change_orders."}},
    "required": ["change_order_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"change_order_id": "540713", "deleted": True}


@tool(
    name="delete_change_order",
    title="Delete change order",
    access="write",
    description="Deletes a change order or change order request for good.",
    details=(
        "Deletes the change order and its items. It cannot be undone. To keep the record, use "
        "update_change_order with status denied instead."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /change-orders/{change_order_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def delete_change_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    change_order_id = str(args["change_order_id"])
    await detail(ctx, change_order_id)
    await service(
        ctx,
        "delete_module_record",
        {"primary_key": int(change_order_id), "module_key": "change_orders", "remove_associated_data": 0},
    )
    return {"change_order_id": change_order_id, "deleted": True}
