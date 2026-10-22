"""Update invoice: status, dates and description of one invoice (invoices/{id}/update)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import INVOICE_STATUSES, plain
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import detail, row_out, update
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_id": {"type": "string", "minLength": 1, "description": "From list_invoices."},
        "status": {"type": "string", "enum": list(INVOICE_STATUSES)},
        "invoice_date": {"type": "string", "format": "date"},
        "due_date": {"type": "string", "format": "date"},
        "description": {"type": "string"},
    },
    "required": ["invoice_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "invoice_id": "2049756",
    "number": "10",
    "status": "submitted",
    "status_name": "Submitted",
    "project_id": "1678167",
    "project_name": "Kitchen Upgrade",
    "customer_id": "6819060",
    "customer_name": "Dana Whitfield (Whitfield Homes)",
    "invoice_date": "2026-10-21",
    "due_date": "2026-11-20",
    "total": 1500.0,
    "balance_due": 1500.0,
    "overdue": False,
    "description": "Progress billing 1 of 3",
}


@tool(
    name="update_invoice",
    title="Update invoice",
    access="write",
    description="Changes an invoice's status, invoice date, due date or description.",
    details=(
        "Sets only the fields you pass. Statuses: draft, submitted (sent to the customer, payments can be "
        "recorded), on_hold, paid, denied, write_off. Contractor Foreman needs a due date on every change, so "
        "an invoice without one needs due_date in the same call. Nobody is emailed. send_invoice does that."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /invoices/{invoice_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def update_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    invoice_id = str(args["invoice_id"])
    fields = {key: args[key] for key in ("invoice_date", "due_date", "description") if key in args}
    if args.get("status"):
        fields["approval_type"] = str(INVOICE_STATUSES[args["status"]])
    if not fields:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    await update(ctx, invoice_id, fields)
    data = await detail(ctx, invoice_id)
    return {**row_out(data), "description": plain(data.get("description"))}
