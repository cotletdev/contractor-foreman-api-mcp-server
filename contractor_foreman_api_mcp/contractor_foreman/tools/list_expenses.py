"""List expenses: Expenses, receipts and costs paid outside bills."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import LIST_PROPS, expense_out, list_records
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
    "expense_id": 3482023,
    "name": "Dump trailer rental",
    "amount": 185.0,
    "date": "2026-10-21",
    "vendor_id": 6819139,
    "vendor": "Dana Whitfield (Triangle Lumber Supply)",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "type": "Material",
    "paid_by": "Sam Ortega",
    "paid_through": None,
    "billable": False,
    "reason": None,
}


@tool(
    name="list_expenses",
    title="List expenses",
    access="read",
    confirm=False,
    description="Expenses with amount, date, vendor, project, cost type and who paid.",
    details=(
        "Reads the Contractor Foreman Expenses list, last added first: name, amount with tax, date, vendor, "
        "project, cost type (Material, Labor, Equipment ...), who paid it and through what, and whether it is "
        "billable to the customer. Filter by project or search."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /expenses",
    example_response={"expenses": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_expenses(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "expenses", None, expense_out)
    return {"expenses": found, "next_cursor": cursor}
