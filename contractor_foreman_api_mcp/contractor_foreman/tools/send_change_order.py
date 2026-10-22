"""Send change order: emails the change order PDF to the customer or given addresses (panel "View/Email PDF")."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._change_orders import customer_email, detail, status_of
from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import emails, send_record
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "change_order_id": {"type": "string", "minLength": 1, "description": "From list_change_orders."},
        "to": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "items": {"type": "string"},
            "description": "Recipient emails. Default: the project's customer.",
        },
        "subject": {"type": "string", "maxLength": 200, "description": "Default: the app's 'Change Order #n'."},
        "message": {"type": "string", "maxLength": 5000, "description": "Email text above the PDF."},
        "copy_me": {"type": "boolean", "default": False},
    },
    "required": ["change_order_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "change_order_id": "540713",
    "sent_to": ["dana@example.com"],
    "subject": "Change Order #235236",
    "status": "open",
}


async def _plan(ctx: ToolContext, args: dict[str, Any]) -> tuple[list[str], str, dict[str, Any]]:
    data = await detail(ctx, str(args["change_order_id"]))
    to = args.get("to") or [email for email in [await customer_email(ctx, data)] if email]
    if not to:
        raise ToolError("The project's customer has no email; pass to.", ErrorCode.INVALID_INPUT)
    return emails(to), args.get("subject") or str(data.get("email_subject") or data.get("subject")), data


async def check_send_change_order(ctx: ToolContext, args: dict[str, Any]) -> None:
    await _plan(ctx, args)


@tool(
    name="send_change_order",
    title="Send change order",
    access="write",
    confirm=True,
    description="Emails the change order as a PDF to the customer or to the addresses you give.",
    details=(
        "Sends the change order (or request) PDF by email from Contractor Foreman, as the panel's View/Email "
        "PDF does. Without to it goes to the project's customer, and a customer without an email stops the "
        "call. The approval call shows recipients and "
        "subject first. The status does not change: update_change_order sets pending_approval or approved. "
        "By default you confirm each call, and you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /change-orders/{change_order_id}/send",
    example_response=EXAMPLE_RESPONSE,
    check=check_send_change_order,
)
async def send_change_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    to, subject, data = await _plan(ctx, args)
    change_order_id = int(args["change_order_id"])
    message = args.get("message", "")
    await send_record(ctx, "change_order", change_order_id, to, subject, message, args.get("copy_me", False))
    return {
        "change_order_id": str(change_order_id),
        "sent_to": to,
        "subject": subject,
        "status": status_of(data.get("type") or "co", data.get("billing_status")),
    }
