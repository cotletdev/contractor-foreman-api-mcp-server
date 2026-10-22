"""Shared pieces of the estimate, change order, invoice, payment and cost item tools (recorded 21.10.2026).

Every call goes through `client.api`, which turns the HTTP-200 sign-out into `auth_expired`. `call` adds the
fields the panel sends with every request and turns the app's own error answers (422 validation, 400, 404,
406, 500, "Cannot POST") into a ToolError. Money is in cents in the app and in dollars in the tools; dates
come as MM/DD/YYYY and go out as YYYY-MM-DD.
"""

from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.client import api
from contractor_foreman_api_mcp.core.errors import AuthExpiredError, ErrorCode, ToolError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# What the panel's web worker adds to every body.
_BASE = {"version": "web", "from": "panel", "timezone": "-0700", "tzid": "America/Los_Angeles", "force_login": 0}

# Global type ids (the `global/types` table, the same on every company, read 21.10.2026).
ITEM_TYPES = {"material": 161, "equipment": 162, "labor": 163, "subcontractor": 164, "other": 165}
ITEM_TYPE_NAMES = {value: key for key, value in ITEM_TYPES.items()}
ESTIMATE_STATUSES = {
    "estimating": "estimate_bidding",
    "pending_approval": "estimate_pending_approval",
    "on_hold": "estimate_on_hold",
    "re_estimating": "estimate_rebid",
    "approved": "estimate_approved",
    "completed": "estimate_completed",
    "lost": "estimate_lost",
}
CHANGE_ORDER_STATUSES = {
    "open": 138,
    "pending_approval": 325,
    "on_hold": 148,
    "approved": 140,
    "denied": 147,
    "billed": 139,
}
REQUEST_STATUSES = {"draft": 256, "on_hold": 257, "approved": 255, "denied": 258, "closed": 320}
INVOICE_STATUSES = {
    "draft": 86,
    "submitted": 146,
    "on_hold": 87,
    "paid": 88,
    "denied": 85,
    "write_off": 141,
}
PAYMENT_TYPES = {"bank_transfer": 244, "cash": 90, "check": 91, "credit_card": 92, "other": 356}
PAYMENT_STATUSES = {"received": 196, "in_review": 198, "verified": 197, "failed": 199}

# Module ids and keys of the send-email call (api/modules/menu-list).
MODULES = {
    "estimate": {"module_id": 15, "module_key": "estimates", "id_key": "estimate_id", "op": "pdf_estimate_customer"},
    "change_order": {
        "module_id": 11,
        "module_key": "change_orders",
        "id_key": "change_order_id",
        "op": "pdf_change_order",
    },
    "invoice": {"module_id": 70, "module_key": "invoice_merge", "id_key": "invoice_id", "op": "pdf_invoice"},
}

_DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


async def call(ctx: ToolContext, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """One panel call with the panel's base fields; the app's error answers become a ToolError."""
    body = await api(ctx, path, {**_BASE, **(payload or {})})
    if str(body.get("need_logout")) == "1":
        raise AuthExpiredError("The app signed this account out. Reconnect it in the console.")
    message = str(body.get("message") or "")
    if message.startswith("Cannot POST") or body.get("success") is False or body.get("statusCode") not in (200, 201):
        text = message.replace("..", ".") if message and not message.startswith("Cannot") else ""
        raise ToolError(text or "Contractor Foreman refused the request.", ErrorCode.TARGET_ERROR)
    return body


def dollars(cents: Any) -> float | None:
    """App amounts are whole cents in strings: '133800' is 1338.00."""
    if cents in (None, ""):
        return None
    try:
        return round(float(cents) / 100, 2)
    except (TypeError, ValueError):
        return None


def cents(amount: float) -> int:
    return round(float(amount) * 100)


def iso(date: Any) -> str | None:
    """MM/DD/YYYY from the app as YYYY-MM-DD; anything else unchanged, empty as None."""
    if not date:
        return None
    match = _DATE.match(str(date))
    return f"{match[3]}-{match[1]}-{match[2]}" if match else str(date)


_TAG = re.compile(r"<[^>]+>")


def plain(value: Any) -> str | None:
    """App text fields may be HTML (terms, notes): the text, None when empty."""
    if not value:
        return None
    text = html.unescape(_TAG.sub(" ", str(value).replace("</p>", "\n")))
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line) or None


def number(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        return None


def key_of(mapping: dict[str, Any], value: Any) -> str | None:
    """Tool name of an app status (key or id), None when the app has one we do not name."""
    return next((name for name, app in mapping.items() if str(app) == str(value)), None)


# Line items as the estimate and change order tools take them.
LINE_ITEM: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Item name shown on the document."},
        "type": {"type": "string", "enum": list(ITEM_TYPES), "default": "other"},
        "quantity": {"type": "number", "minimum": 0, "default": 1},
        "unit": {"type": "string", "description": "e.g. ea, hr, sq ft, ls.", "default": "ea"},
        "unit_cost": {"type": "number", "minimum": 0, "description": "Your cost per unit in dollars."},
        "markup_percent": {"type": "number", "minimum": 0, "default": 0},
        "cost_code_id": {"type": "string", "description": "From list_cost_codes."},
        "description": {"type": "string", "description": "Shown under the item."},
    },
    "required": ["name", "unit_cost"],
    "additionalProperties": False,
}


def item_in(item: dict[str, Any], section_id: Any, position: int, number_key: str) -> dict[str, Any]:
    """One line item as the estimate and change order item calls take it (unit cost in cents)."""
    return {
        "subject": item["name"],
        "quantity": item.get("quantity", 1),
        "unit": item.get("unit", "ea"),
        "unit_cost": cents(item["unit_cost"]),
        "markup": str(item.get("markup_percent", 0)),
        "is_markup_percentage": 1,
        "hidden_markup": 0,
        "item_type": str(ITEM_TYPES[item.get("type", "other")]),
        "cost_code_id": str(item.get("cost_code_id") or ""),
        "description": item.get("description", ""),
        "apply_global_tax": 1,
        "section_id": section_id,
        number_key: position,
    }


def item_out(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": str(item.get("item_id")),
        "name": item.get("subject"),
        "type": ITEM_TYPE_NAMES.get(number(item.get("item_type")) or 0),
        "quantity": item.get("quantity"),
        "unit": item.get("unit") or None,
        "unit_cost": dollars(item.get("unit_cost")),
        "markup_percent": float(item["markup"]) if item.get("is_markup_percentage") and item.get("markup") else None,
        "total": dollars(item.get("total")),
        "cost_code": item.get("cost_code_name") or None,
        "description": item.get("description") or None,
        "section": item.get("section_name") or None,
    }


def emails(values: list[str]) -> list[str]:
    bad = [value for value in values if not _EMAIL.match(value)]
    if bad:
        raise ToolError(f"Not an email address: {', '.join(bad)}.", ErrorCode.INVALID_INPUT)
    return values


async def send_record(
    ctx: ToolContext, kind: str, record_id: int, to: list[str], subject: str, message: str, copy_me: bool
) -> None:
    """The panel's "View/Email PDF" send: the record's customer PDF to the given addresses.

    `send_custom_email: 0` is what that drawer sends. With 1 (the free-text drawer) the change order and
    invoice path checks a reCAPTCHA token; this path does not, so no CAPTCHA is solved.
    """
    module = MODULES[kind]
    await call(
        ctx,
        "common/send-email",
        {
            "op": module["op"],
            "action": "send",
            "module_id": module["module_id"],
            "module_key": module["module_key"],
            "record_id": record_id,
            module["id_key"]: record_id,
            "emails": to,
            "selected_user_arr": [],
            "custom_subject": subject,
            "custom_msg": "".join(f"<p>{line}</p>" for line in message.splitlines() if line.strip()),
            "send_me_copy": 1 if copy_me else 0,
            "send_custom_email": 0,
            "g-recaptcha-response": "",
            "save_file_to_folder": 0,
            **({"ViewPDFOnly": 1} if kind == "estimate" else {}),
        },
    )


async def share_link(ctx: ToolContext, kind: str, record_id: int) -> str:
    pages = {"estimate": "manage-estimates", "change_order": "manage-change-orders", "invoice": "manage-invoice"}
    body = await call(
        ctx,
        "common/generate-share-link",
        {
            "record_id": record_id,
            "module_key": MODULES[kind]["module_key"],
            "module_page": pages[kind],
            "is_custom_deep_link": 1,
        },
    )
    return str((body.get("data") or {}).get("short_link") or "")


async def project_customer(ctx: ToolContext, project_id: int) -> int:
    """The customer of a project (projects/get-details)."""
    body = await call(ctx, "projects/get-details", {"project_id": project_id, "record_type": "project"})
    data = body.get("data") or {}
    customer = number(data.get("customer_id"))
    if not customer:
        raise ToolError("This project has no customer; pass customer_id.", ErrorCode.INVALID_INPUT)
    return customer


async def delete_record(ctx: ToolContext, module_key: str, record_id: int) -> None:
    await call(ctx, "common/delete", {"remove_associated_data": 0, "record_id": record_id, "module_key": module_key})


async def service(ctx: ToolContext, op: str, params: dict[str, Any]) -> dict[str, Any]:
    """`common/service` (the old PHP actions) wants the company and user ids, or answers 401 "Invalid Token!".

    The ids come from `get-app-data` on every call: `ctx.cache_*` is shared by all accounts of the app.
    """
    # get-app-data has no statusCode of its own, so it goes past `call`.
    me = ((await api(ctx, "get-app-data", {})).get("data") or {}).get("user") or {}
    me = me.get("data") or {}
    payload = {"op": op, "company_id": me.get("company_id"), "user_id": me.get("user_id"), **params}
    body = await api(ctx, "common/service", {**_BASE, "iframe_call": 0, "global_project": "", **payload})
    if body.get("success") not in (True, 1, "1"):
        message = str(body.get("message") or "")
        raise ToolError(message or "Contractor Foreman refused the request.", ErrorCode.TARGET_ERROR)
    return body
