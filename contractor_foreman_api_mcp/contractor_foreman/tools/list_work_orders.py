"""List work orders: Work Orders for extra or change work."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import work_order_out
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import LIST_PROPS, list_records
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
    "work_order_id": 300754,
    "number": "3",
    "subject": "Replace damaged ceiling tiles in dining room",
    "description": None,
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "customer_id": 6819089,
    "customer": "Jacob Carver (Jacob & Co.)",
    "status": "Open",
    "start_date": "2026-10-22",
    "end_date": "2026-10-23",
    "total": 0.0,
    "assigned_to": None,
    "issued_by": "Sam Ortega",
}


@tool(
    name="list_work_orders",
    title="List work orders",
    access="read",
    confirm=False,
    description="Work orders with project, customer, status, dates, total and assignee.",
    details=(
        "Reads the Contractor Foreman Work Orders list, newest first: number, subject, description, project, "
        "customer, status (Open, Estimating, Submitted, Approved, Canceled, Completed), start and end date, "
        "total and who it is assigned to. Filter by project or search."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /work-orders",
    example_response={"work_orders": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_work_orders(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "workorder/get-workorder-list", "workOrders", work_order_out)
    return {"work_orders": found, "next_cursor": cursor}
