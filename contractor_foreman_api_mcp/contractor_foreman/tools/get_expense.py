"""Get expense: one expense record."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import expense_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"expense_id": {"type": "integer", "description": "expense_id from list_expenses."}},
    "required": ["expense_id"],
    "additionalProperties": False,
}

EXAMPLE_EXPENSE: dict[str, Any] = {
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
    "reason": "Haul-off of demolition debris",
    "cost_code": None,
}


async def read_expense(ctx: ToolContext, expense_id: int) -> dict[str, Any]:
    row = first_record(await call(ctx, "expenses/get-expense-detail", {"expense_id": expense_id}))
    if not row.get("expense_id"):
        raise ToolError("Contractor Foreman did not find that expense.", ErrorCode.TARGET_ERROR)
    out = expense_out(row, await date_format(ctx))
    out["cost_code"] = text(row.get("cost_code_name"))
    return out


@tool(
    name="get_expense",
    title="Get expense",
    access="read",
    confirm=False,
    description="One expense with amount, date, vendor, project, cost type, cost code and reason.",
    details=(
        "Reads one Contractor Foreman expense by expense_id: what list_expenses gives plus the cost code and "
        "the reason written on it."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /expenses/{expense_id}",
    example_response=EXAMPLE_EXPENSE,
)
async def get_expense(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_expense(ctx, args["expense_id"])
