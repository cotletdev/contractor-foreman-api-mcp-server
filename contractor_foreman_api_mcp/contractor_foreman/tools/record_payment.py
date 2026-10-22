"""Record payment: a payment received against a submitted invoice (common/add-payment)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    INVOICE_STATUSES,
    PAYMENT_STATUSES,
    PAYMENT_TYPES,
    call,
    cents,
    dollars,
    key_of,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import detail, payments
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_id": {"type": "string", "minLength": 1, "description": "From list_invoices."},
        "amount": {"type": "number", "exclusiveMinimum": 0, "description": "Dollars, at most the balance due."},
        "method": {"type": "string", "enum": list(PAYMENT_TYPES)},
        "date": {"type": "string", "format": "date", "description": "Default: today."},
        "status": {"type": "string", "enum": list(PAYMENT_STATUSES), "default": "received"},
        "notes": {"type": "string", "maxLength": 1000, "description": "e.g. the check number."},
    },
    "required": ["invoice_id", "amount", "method"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "payment_id": "3621588",
    "invoice_id": "2049756",
    "amount": 500.0,
    "method": "check",
    "date": "2026-10-21",
    "status": "received",
    "balance_due": 1000.0,
    "invoice_status": "submitted",
}


@tool(
    name="record_payment",
    title="Record payment",
    access="write",
    description="Records a payment you received against an invoice.",
    details=(
        "Adds a payment to an invoice, as Add Payment does: amount in dollars, method (bank_transfer, cash, "
        "check, credit_card, other), date, status (received, in_review, verified, failed) and notes. It only "
        "records money already received. It charges nobody and emails nobody. The invoice must be submitted "
        "(update_invoice) and the amount cannot exceed the balance due. A payment that clears the balance "
        "marks the invoice paid."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /invoices/{invoice_id}/payments",
    example_response=EXAMPLE_RESPONSE,
)
async def record_payment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    invoice_id = str(args["invoice_id"])
    data = await detail(ctx, invoice_id)
    if str(data.get("approval_type")) != str(INVOICE_STATUSES["submitted"]):
        raise ToolError(
            f"The invoice is {data.get('approval_type_name') or 'not submitted'}; payments need a submitted "
            "invoice (update_invoice status submitted).",
            ErrorCode.INVALID_INPUT,
        )
    balance = dollars(data.get("due_balance")) or 0.0
    if args["amount"] > balance + 0.001:
        raise ToolError(f"The balance due is {balance:.2f}; the amount cannot be more.", ErrorCode.INVALID_INPUT)
    date = args.get("date") or datetime.datetime.now(tz=datetime.UTC).date().isoformat()
    body = await call(
        ctx,
        "common/add-payment",
        {
            "invoice_id": invoice_id,
            "payment_date": date,
            "amount": str(cents(args["amount"])),
            "payment_type": str(PAYMENT_TYPES[args["method"]]),
            "approval_status": PAYMENT_STATUSES[args.get("status", "received")],
            "access_to_custom_fields": 0,
            **({"payment_notes": args["notes"]} if args.get("notes") else {}),
        },
    )
    payment_id = str((body.get("data") or {}).get("id") or "")
    after = await detail(ctx, invoice_id)
    saved = next((row for row in await payments(ctx, invoice_id) if row["payment_id"] == payment_id), {})
    return {
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "amount": saved.get("amount", args["amount"]),
        "method": args["method"],
        "date": saved.get("date", date),
        "status": saved.get("status", args.get("status", "received")),
        "balance_due": dollars(after.get("due_balance")) or 0.0,
        "invoice_status": key_of(INVOICE_STATUSES, after.get("approval_type")),
    }
