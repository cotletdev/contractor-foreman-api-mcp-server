"""Get work order: one work order with its items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import work_order_out
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import item_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"work_order_id": {"type": "integer", "description": "work_order_id from list_work_orders."}},
    "required": ["work_order_id"],
    "additionalProperties": False,
}

EXAMPLE_WO: dict[str, Any] = {
    "work_order_id": 300754,
    "number": "3",
    "subject": "Replace damaged ceiling tiles in dining room",
    "description": "Remove and replace 12 water-stained ceiling tiles; match existing 2x2 grid.",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "customer_id": 6819089,
    "customer": "Jacob Carver (Jacob & Co.)",
    "status": "Open",
    "start_date": "2026-10-22",
    "end_date": "2026-10-23",
    "total": 0.0,
    "assigned_to": None,
    "issued_by": "Michael Howard",
    "location": None,
    "notes": None,
    "items": [],
}


async def read_work_order(ctx: ToolContext, work_order_id: int) -> dict[str, Any]:
    row = first_record(await call(ctx, "workorder/get-workorder-details", {"id": work_order_id}))
    if not row.get("work_order_id"):
        raise ToolError("Contractor Foreman did not find that work order.", ErrorCode.TARGET_ERROR)
    out = work_order_out(row, await date_format(ctx))
    out["location"] = text(row.get("location"))
    out["notes"] = text(row.get("notes"))
    items = await call(ctx, f"workorder/{work_order_id}/getWorkorderItem")
    data = items.get("data")
    found = data.get("items") if isinstance(data, dict) else data
    out["items"] = [item_out(i) for i in found or [] if isinstance(i, dict)]
    return out


@tool(
    name="get_work_order",
    title="Get work order",
    access="read",
    confirm=False,
    description="One work order with project, customer, status, dates, location, notes and items.",
    details=(
        "Reads one Contractor Foreman work order by work_order_id: what list_work_orders gives plus the location, "
        "notes and line items with quantity, unit cost and total."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /work-orders/{work_order_id}",
    example_response={
        **EXAMPLE_WO,
        "total": 360.0,
        "items": [
            {
                "item_id": 2502140,
                "description": "Ceiling tile, 2x2 lay-in",
                "type": "material",
                "quantity": 12,
                "unit": "ea",
                "unit_cost": 30.0,
                "total": 360.0,
                "cost_code": None,
            }
        ],
    },
)
async def get_work_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_work_order(ctx, args["work_order_id"])
