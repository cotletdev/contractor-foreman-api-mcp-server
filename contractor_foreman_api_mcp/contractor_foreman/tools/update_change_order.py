"""Update change order: status, title, reason or date of a change order or request (change-orders/update-detail)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._change_orders import STATUS_NAMES, detail, row_out, status_id
from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import call, plain
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "change_order_id": {"type": "string", "minLength": 1, "description": "From list_change_orders."},
        "status": {"type": "string", "enum": STATUS_NAMES},
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "description": {"type": "string"},
        "date": {"type": "string", "format": "date"},
    },
    "required": ["change_order_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "change_order_id": "540713",
    "number": "235236",
    "title": "Add under-cabinet lighting",
    "kind": "change_order",
    "status": "approved",
    "status_name": "Unbilled/Approved",
    "project_id": "1678167",
    "project_name": "Kitchen Upgrade",
    "customer_name": "Dana Whitfield (Whitfield Homes)",
    "date": "2026-10-21",
    "total": 680.4,
    "description": "Client request on 20 Oct: add LED lighting under the new upper cabinets.",
}


@tool(
    name="update_change_order",
    title="Update change order",
    access="write",
    description="Changes a change order's status, title, reason or date.",
    details=(
        "Sets only the fields you pass. Change order statuses: open, pending_approval, on_hold, approved "
        "(Unbilled/Approved, counts toward the contract), denied, billed. Change order request statuses: "
        "draft, on_hold, approved, denied, closed. A status of the other kind stops the call. Nobody is "
        "emailed. send_change_order does that."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /change-orders/{change_order_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def update_change_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    change_order_id = str(args["change_order_id"])
    data = await detail(ctx, change_order_id)
    kind = data.get("type") or "co"
    fields: dict[str, Any] = {}
    if args.get("status"):
        fields["billing_status"] = status_id(kind, args["status"])
    for name, key in (("title", "subject"), ("description", "notes"), ("date", "order_date")):
        if name in args:
            fields[key] = args[name]
    if not fields:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    await call(
        ctx,
        "change-orders/update-detail",
        {"change_order_id": int(change_order_id), "project_id": data.get("project_id"), "type": kind, "items": fields},
    )
    data = await detail(ctx, change_order_id)
    return {**row_out(data), "description": plain(data.get("notes"))}
