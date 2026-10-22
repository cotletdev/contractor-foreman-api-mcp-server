"""Create change order: a change order or request on a project, with its reason and priced line items."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._change_orders import add_items, detail, full_out, sections
from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import LINE_ITEM, call, number
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "minLength": 1, "description": "From list_projects."},
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "items": {"type": "array", "maxItems": 100, "items": LINE_ITEM},
        "description": {"type": "string", "description": "Why it changes: who asked, when, what."},
        "kind": {
            "type": "string",
            "enum": ["change_order", "request"],
            "default": "change_order",
            "description": "request = a change order request (COR) to price before it becomes a change order.",
        },
        "number": {
            "type": "string",
            "maxLength": 30,
            "description": "Your own number. Default: the app's next, or COR-<requests on the project + 1>.",
        },
        "date": {"type": "string", "format": "date", "description": "Default: today."},
    },
    "required": ["project_id", "title"],
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


async def _request_number(ctx: ToolContext, project: int) -> str:
    """The app numbers change orders itself but wants a COR# from the user: COR-<requests on the project + 1>."""
    filters = {"status": "", "project": str(project), "type": "cor"}
    body = await call(
        ctx, "change-orders/get-list", {"page": 0, "limit": 500, "type": "cor", "ignore_filter": 1, "filter": filters}
    )
    return f"COR-{len((body.get('data') or {}).get('changeOrders') or []) + 1}"


@tool(
    name="create_change_order",
    title="Create change order",
    access="write",
    description="Creates a change order or change order request on a project, with line items.",
    details=(
        "Saves a new change order (status open) or change order request (status draft) on a project, for "
        "the project's customer. description records the reason. items are priced lines (name, type, "
        "quantity, unit, unit cost in dollars, markup percent, cost code). The app computes the total. "
        "Nothing is sent. send_change_order emails it after your OK, update_change_order sets the status."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /change-orders",
    example_response=EXAMPLE_RESPONSE,
)
async def create_change_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    kind = "cor" if args.get("kind") == "request" else "co"
    project = number(args["project_id"])
    if not project:
        raise ToolError("project_id must be a project id from list_projects.", ErrorCode.INVALID_INPUT)
    payload: dict[str, Any] = {
        "project_id": project,
        "subject": args["title"],
        "custom_change_order_id": args.get("number") or (await _request_number(ctx, project) if kind == "cor" else ""),
        "type": kind,
        "access_to_custom_fields": 0,
        "order_date": args.get("date") or datetime.datetime.now(tz=datetime.UTC).date().isoformat(),
    }
    body = await call(ctx, "change-orders/add", payload)
    change_order_id = str((body.get("data") or {}).get("changeOrderId") or "")
    if not number(change_order_id):
        raise ToolError("Contractor Foreman did not return the new change order.", ErrorCode.TARGET_ERROR)
    if args.get("description"):
        await call(
            ctx,
            "change-orders/update-detail",
            {
                "change_order_id": int(change_order_id),
                "project_id": project,
                "type": kind,
                "items": {"notes": args["description"]},
            },
        )
    if args.get("items"):
        await add_items(ctx, change_order_id, args["items"])
    return full_out(await detail(ctx, change_order_id), await sections(ctx, change_order_id))
