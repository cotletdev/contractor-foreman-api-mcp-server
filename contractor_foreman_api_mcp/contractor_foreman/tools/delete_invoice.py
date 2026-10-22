"""Delete invoice: removes one invoice (common/delete, module invoice_merge)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import delete_record
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import detail, payments
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"invoice_id": {"type": "string", "minLength": 1, "description": "From list_invoices."}},
    "required": ["invoice_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"invoice_id": "2049756", "deleted": True}


@tool(
    name="delete_invoice",
    title="Delete invoice",
    access="write",
    description="Deletes an invoice that has no payments, for good.",
    details=(
        "Deletes the invoice and its items. It cannot be undone. An invoice with payments recorded is "
        "refused. For that one, or to keep the record, use update_invoice with status write_off or denied."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /invoices/{invoice_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def delete_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    invoice_id = str(args["invoice_id"])
    await detail(ctx, invoice_id)
    if await payments(ctx, invoice_id):
        raise ToolError("This invoice has payments recorded; it is not deleted.", ErrorCode.INVALID_INPUT)
    await delete_record(ctx, "invoice_merge", int(invoice_id))
    return {"invoice_id": invoice_id, "deleted": True}
