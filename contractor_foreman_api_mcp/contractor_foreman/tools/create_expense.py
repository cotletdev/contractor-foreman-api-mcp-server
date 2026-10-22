"""Create expense: Expenses, Add."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    call,
    created_id,
    to_cents,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import ITEM_TYPES
from contractor_foreman_api_mcp.contractor_foreman.tools.get_expense import EXAMPLE_EXPENSE, read_expense
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 200, "description": "What was bought or paid."},
        "amount": {"type": "number", "exclusiveMinimum": 0, "description": "In the account currency."},
        "date": {**DATE_SCHEMA, "description": "YYYY-MM-DD. Default: today."},
        "vendor_id": {"type": "integer", "description": "The vendor's contact_id (list_contacts type vendor)."},
        "project_id": {
            "type": "integer",
            "description": "The project the cost belongs to (list_projects). The app refuses an expense without one.",
        },
        "type": {"type": "string", "enum": list(ITEM_TYPES), "default": "material"},
        "reason": {"type": "string", "maxLength": 2000},
        "billable": {"type": "boolean", "default": False, "description": "Bill it on to the customer."},
    },
    "required": ["name", "amount", "project_id"],
    "additionalProperties": False,
}


@tool(
    name="create_expense",
    title="Create expense",
    access="write",
    confirm=False,
    description="Records an expense (receipt, purchase, fee) with amount, date, vendor and project.",
    details=(
        "Enters an expense in Contractor Foreman as the signed-in user: name, amount, date, vendor, project, cost "
        "type, reason and whether it is billable to the customer. The project is required by the app, and the "
        "expense shows in that project's job costing. No receipt file is attached. Returns the saved expense."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /expenses",
    example_response=EXAMPLE_EXPENSE,
)
async def create_expense(ctx: ToolContext, args: dict[str, Any]) -> Any:
    payload: dict[str, Any] = {
        "expense_name": args["name"].strip(),
        "amount": to_cents(args["amount"]),
        "item_type": ITEM_TYPES[args.get("type") or "material"],
        "is_billable": 1 if args.get("billable") else 0,
        "access_to_custom_fields": 0,
    }
    if args.get("vendor_id"):
        payload["directory_id"] = args["vendor_id"]
    payload["project_id"] = str(args["project_id"])
    expense_id = created_id(await call(ctx, "expenses/create-expense", payload), "expense_id")
    # The add form keeps today's date and no reason; the panel saves both as field edits, dates as YYYY-MM-DD.
    update: dict[str, Any] = {}
    if args.get("date"):
        update["expense_date"] = args["date"]
    if args.get("reason"):
        update["reason"] = args["reason"].strip()
    if update:
        await call(ctx, "expenses/update-expense-detail", {"expense_id": expense_id, **update})
    return await read_expense(ctx, expense_id)
