"""Invoice shapes shared by the invoice and payment tools (recorded 21.10.2026).

Invoices answer to `invoices` (list, `page`/`length`, 0-based page), `invoices/{id}` (detail),
`invoices/{id}/get-invoice-items` and `invoices/{id}/get-payments`. Status is `approval_type`, an id
from INVOICE_STATUSES; the app only takes payments on a submitted invoice.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    INVOICE_STATUSES,
    PAYMENT_STATUSES,
    PAYMENT_TYPES,
    call,
    dollars,
    iso,
    item_in,
    item_out,
    key_of,
    number,
    plain,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext


# Invoice payment rows name the method by key, the payments list by id.
_PAYMENT_TYPE_KEYS = {
    "bank_transfer": "payment_bank_transfer",
    "cash": "payment_cash",
    "check": "payment_cheque",
    "credit_card": "payment_credit_card",
    "other": "payment_other",
}


def _overdue(due: str | None, balance: float | None, status: str | None) -> bool:
    if not due or not balance or status in ("draft", "paid", "write_off", "denied"):
        return False
    return due < datetime.datetime.now(tz=datetime.UTC).date().isoformat()


def row_out(row: dict[str, Any]) -> dict[str, Any]:
    # The list carries the stored status in original_approval_type, the detail in approval_type.
    status = key_of(INVOICE_STATUSES, row.get("original_approval_type") or row.get("approval_type"))
    due = iso(row.get("due_date"))
    balance = dollars(row.get("due_balance"))
    return {
        "invoice_id": str(row.get("invoice_id")),
        "number": row.get("prefix_company_invoice_id") or row.get("company_invoice_id"),
        "status": status,
        "status_name": row.get("approval_type_name"),
        "project_id": str(row["project_id"]) if number(row.get("project_id")) else None,
        "project_name": row.get("project_name"),
        "customer_id": str(row["customer_id"]) if number(row.get("customer_id")) else None,
        "customer_name": plain(row.get("customer_name")),
        "invoice_date": iso(row.get("invoice_date")),
        "due_date": due,
        "total": dollars(row.get("total")) or 0.0,
        "balance_due": balance if balance is not None else 0.0,
        "overdue": _overdue(due, balance, status),
    }


def payment_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "payment_id": str(row.get("payment_id")),
        "date": iso(row.get("payment_date")),
        "amount": dollars(row.get("amount")) or 0.0,
        "method": key_of(PAYMENT_TYPES, row.get("payment_type"))
        or key_of(_PAYMENT_TYPE_KEYS, row.get("payment_type_key"))
        or plain(row.get("payment_type_name")),
        "status": key_of(PAYMENT_STATUSES, row.get("approval_status")) or plain(row.get("approval_status_name")),
        "notes": plain(row.get("payment_notes")),
        "invoice_id": str(row["invoice_id"]) if number(row.get("invoice_id")) else None,
        "invoice_number": row.get("company_invoice_id"),
    }


async def detail(ctx: ToolContext, invoice_id: str) -> dict[str, Any]:
    data = (await call(ctx, f"invoices/{int(invoice_id)}", {})).get("data")
    if not data:
        raise ToolError("No such invoice.", ErrorCode.INVALID_INPUT)
    return data


async def payments(ctx: ToolContext, invoice_id: str) -> list[dict[str, Any]]:
    body = await call(ctx, f"invoices/{int(invoice_id)}/get-payments", {"get_payment_link": 0})
    return [payment_out(row) for row in (body.get("data") or {}).get("payments") or []]


async def add_items(ctx: ToolContext, invoice_id: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Plain priced lines at the end of the invoice (invoices/{id}/add-invoice-items)."""
    current = (await call(ctx, f"invoices/{int(invoice_id)}/get-invoice-items", {"data_for": "all"})).get("data") or {}
    start = len(current.get("items") or [])
    payload = []
    for i, item in enumerate(items):
        row = item_in(item, None, start + i + 1, "invoice_item_no")
        row.pop("section_id")
        payload.append(row)
    await call(ctx, f"invoices/{int(invoice_id)}/add-invoice-items", {"invoice_id": int(invoice_id), "items": payload})
    # The add answer leaves out most item fields; the item list has them, the new ones last.
    after = (await call(ctx, f"invoices/{int(invoice_id)}/get-invoice-items", {"data_for": "all"})).get("data") or {}
    return [item_out(row) for row in (after.get("items") or [])[start:]]


async def update(ctx: ToolContext, invoice_id: str, fields: dict[str, Any]) -> None:
    """invoices/{id}/update wants due_date on every call: the current one unless it changes."""
    if "due_date" not in fields:
        due = iso((await detail(ctx, invoice_id)).get("due_date"))
        if not due:
            raise ToolError("This invoice has no due date yet; pass due_date.", ErrorCode.INVALID_INPUT)
        fields = {**fields, "due_date": due}
    await call(ctx, f"invoices/{int(invoice_id)}/update", fields)
