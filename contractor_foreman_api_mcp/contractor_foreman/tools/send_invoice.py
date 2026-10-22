"""Send invoice: emails the invoice PDF to the customer or given addresses (panel "View/Email PDF")."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import emails, plain, send_record
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import detail, row_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_id": {"type": "string", "minLength": 1, "description": "From list_invoices or create_invoice."},
        "to": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "items": {"type": "string"},
            "description": "Recipient emails. Default: the invoice's customer.",
        },
        "subject": {"type": "string", "maxLength": 200, "description": "Default: the app's 'Invoice #n'."},
        "message": {"type": "string", "maxLength": 5000, "description": "Email text above the PDF."},
        "copy_me": {"type": "boolean", "default": False},
    },
    "required": ["invoice_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "invoice_id": "2049756",
    "sent_to": ["dana@example.com"],
    "subject": "Invoice #10",
    "status": "submitted",
    "balance_due": 1000.0,
}


async def _plan(ctx: ToolContext, args: dict[str, Any]) -> tuple[list[str], str, dict[str, Any]]:
    data = await detail(ctx, str(args["invoice_id"]))
    if not data.get("due_date"):
        raise ToolError(
            "Set a due date first (update_invoice); the app does not email without one.", ErrorCode.INVALID_INPUT
        )
    customer = data.get("customer") or {}
    default = plain(data.get("customer_email") or customer.get("email"))
    to = args.get("to") or ([default] if default else [])
    if not to:
        raise ToolError("The invoice's customer has no email; pass to.", ErrorCode.INVALID_INPUT)
    return emails(to), args.get("subject") or str(data.get("email_subject") or "Invoice"), data


async def check_send_invoice(ctx: ToolContext, args: dict[str, Any]) -> None:
    await _plan(ctx, args)


@tool(
    name="send_invoice",
    title="Send invoice",
    access="write",
    confirm=True,
    description="Emails the invoice as a PDF to the customer or to the addresses you give.",
    details=(
        "Sends the invoice PDF by email from Contractor Foreman, as the panel's View/Email PDF does. Without "
        "to it goes to the invoice's customer, and a customer without an email stops the call. The approval "
        "call shows recipients and subject first. The invoice needs a due date (update_invoice). Sending does "
        "not change the status: update_invoice with status submitted marks it sent. By default you confirm "
        "each call, and you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /invoices/{invoice_id}/send",
    example_response=EXAMPLE_RESPONSE,
    check=check_send_invoice,
)
async def send_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    to, subject, data = await _plan(ctx, args)
    invoice_id = int(args["invoice_id"])
    await send_record(ctx, "invoice", invoice_id, to, subject, args.get("message", ""), args.get("copy_me", False))
    row = row_out(data)
    return {
        "invoice_id": str(invoice_id),
        "sent_to": to,
        "subject": subject,
        "status": row["status"],
        "balance_due": row["balance_due"],
    }
