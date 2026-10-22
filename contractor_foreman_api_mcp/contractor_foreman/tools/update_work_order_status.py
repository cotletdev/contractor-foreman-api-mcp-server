"""Update work order status: the status field on a work order."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, status_id
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import WORK_ORDER_KEYS, WORK_ORDER_STATUSES
from contractor_foreman_api_mcp.contractor_foreman.tools.get_work_order import EXAMPLE_WO, read_work_order
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "work_order_id": {"type": "integer", "description": "work_order_id from list_work_orders."},
        "status": {"type": "string", "enum": WORK_ORDER_STATUSES},
    },
    "required": ["work_order_id", "status"],
    "additionalProperties": False,
}


@tool(
    name="update_work_order_status",
    title="Update work order status",
    access="write",
    confirm=False,
    description="Moves a work order to open, estimating, submitted, approved, canceled or completed.",
    details=(
        "Sets the status of a Contractor Foreman work order as the status field on its page does. The status in "
        "the answer is the label the company uses for it. Nobody is emailed. Returns the work order as saved."
    ),
    input_schema=INPUT_SCHEMA,
    route="PUT /work-orders/{work_order_id}/status",
    example_response={**EXAMPLE_WO, "status": "Completed"},
)
async def update_work_order_status(ctx: ToolContext, args: dict[str, Any]) -> Any:
    wanted = await status_id(ctx, "work_order_status", WORK_ORDER_KEYS[args["status"]])
    await call(ctx, f"workorder/{args['work_order_id']}/update", {"work_order_status": wanted})
    return await read_work_order(ctx, args["work_order_id"])
