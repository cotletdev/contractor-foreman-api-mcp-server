"""Send estimate: emails the estimate PDF to the customer or given addresses (the panel's "View/Email PDF")."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    ESTIMATE_STATUSES,
    call,
    emails,
    key_of,
    plain,
    send_record,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "estimate_id": {"type": "string", "minLength": 1, "description": "From list_estimates or create_estimate."},
        "to": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "items": {"type": "string"},
            "description": "Recipient emails. Default: the estimate's customer.",
        },
        "subject": {"type": "string", "maxLength": 200, "description": "Default: the app's 'Estimate: <title> (#n)'."},
        "message": {"type": "string", "maxLength": 5000, "description": "Email text above the PDF."},
        "copy_me": {"type": "boolean", "default": False, "description": "Send a copy to you."},
    },
    "required": ["estimate_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "estimate_id": "1616575",
    "sent_to": ["dana@example.com"],
    "subject": "Estimate: Pantry Cabinet Addition (#5)",
    "status": "estimating",
}


async def _plan(ctx: ToolContext, args: dict[str, Any]) -> tuple[list[str], str, dict[str, Any]]:
    data = (await call(ctx, f"estimate/{args['estimate_id']}/detail", {})).get("data") or {}
    to = args.get("to") or [email for email in [plain(data.get("customer_email"))] if email]
    if not to:
        raise ToolError("The estimate's customer has no email; pass to.", ErrorCode.INVALID_INPUT)
    return emails(to), args.get("subject") or str(data.get("email_subject") or data.get("title")), data


async def check_send_estimate(ctx: ToolContext, args: dict[str, Any]) -> None:
    await _plan(ctx, args)


@tool(
    name="send_estimate",
    title="Send estimate",
    access="write",
    confirm=True,
    description="Emails the estimate as a PDF to the customer or to the addresses you give.",
    details=(
        "Sends the customer version of the estimate PDF by email from Contractor Foreman, as the panel's "
        "View/Email PDF does. Without to it goes to the estimate's customer, and a customer without an email "
        "stops the call. The approval call shows the recipients and subject first. The estimate's status does "
        "not change. update_estimate sets it (pending_approval, approved). By default you confirm each call, "
        "and you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /estimates/{estimate_id}/send",
    example_response=EXAMPLE_RESPONSE,
    check=check_send_estimate,
)
async def send_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    to, subject, data = await _plan(ctx, args)
    estimate_id = int(args["estimate_id"])
    await send_record(ctx, "estimate", estimate_id, to, subject, args.get("message", ""), args.get("copy_me", False))
    status = key_of(ESTIMATE_STATUSES, data.get("approval_type_key"))
    return {"estimate_id": str(estimate_id), "sent_to": to, "subject": subject, "status": status}
