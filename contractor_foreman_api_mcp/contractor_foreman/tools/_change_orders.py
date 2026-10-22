"""Change order reads and item writes shared by the change order tools (recorded 21.10.2026).

A change order (`type` co) or a change order request (`type` cor) belongs to a project. Its status is
`billing_status`, an id from two lists: CHANGE_ORDER_STATUSES for co, REQUEST_STATUSES for cor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    CHANGE_ORDER_STATUSES,
    REQUEST_STATUSES,
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

STATUS_NAMES = sorted(set(CHANGE_ORDER_STATUSES) | set(REQUEST_STATUSES))


def status_of(kind: str, value: Any) -> str | None:
    return key_of(REQUEST_STATUSES if kind == "cor" else CHANGE_ORDER_STATUSES, value)


def status_id(kind: str, status: str) -> int:
    statuses = REQUEST_STATUSES if kind == "cor" else CHANGE_ORDER_STATUSES
    if status not in statuses:
        label = "a change order request" if kind == "cor" else "a change order"
        raise ToolError(f"Status of {label} is one of: {', '.join(statuses)}.", ErrorCode.INVALID_INPUT)
    return statuses[status]


def row_out(row: dict[str, Any]) -> dict[str, Any]:
    kind = row.get("type") or "co"
    return {
        "change_order_id": str(row.get("change_order_id")),
        "number": row.get("prefix_company_order_id") or row.get("company_order_id"),
        "title": row.get("subject"),
        "kind": "request" if kind == "cor" else "change_order",
        "status": status_of(kind, row.get("billing_status")),
        "status_name": row.get("billing_status_name"),
        "project_id": str(row["project_id"]) if number(row.get("project_id")) else None,
        "project_name": row.get("project_name"),
        "customer_name": plain(row.get("customer_name")),
        "date": iso(row.get("order_date")),
        "total": dollars(row.get("total")) or 0.0,
    }


async def detail(ctx: ToolContext, change_order_id: str) -> dict[str, Any]:
    data = (await call(ctx, "change-orders/get-order-detail", {"change_order_id": int(change_order_id)})).get("data")
    if not data:
        raise ToolError("No such change order.", ErrorCode.INVALID_INPUT)
    return data


async def sections(ctx: ToolContext, change_order_id: str) -> list[dict[str, Any]]:
    body = await call(ctx, "change-orders/get-items", {"change_order_id": int(change_order_id), "need_section": 1})
    return body.get("data") or []


def full_out(data: dict[str, Any], parts: list[dict[str, Any]]) -> dict[str, Any]:
    items = [item_out(item) for part in parts for item in part.get("items") or []]
    return {
        **row_out(data),
        "description": plain(data.get("notes")),
        "customer_id": str(data["customer_id"]) if number(data.get("customer_id")) else None,
        "estimate_id": str(data["estimate_id"]) if number(data.get("estimate_id")) else None,
        "time_delay_days": data.get("day_delay") or None,
        "items": items,
        "sections": [{"section_id": str(part.get("section_id")), "name": part.get("section_name")} for part in parts],
    }


async def add_items(ctx: ToolContext, change_order_id: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parts = await sections(ctx, change_order_id)
    if not parts:
        raise ToolError("This change order has no section to add items to.", ErrorCode.TARGET_ERROR)
    start = sum(len(part.get("items") or []) for part in parts)
    section_id = parts[0]["section_id"]
    payload = [item_in(item, section_id, start + i + 1, "order_item_no") for i, item in enumerate(items)]
    saved = await call(ctx, "change-orders/add-items", {"change_order_id": int(change_order_id), "items": payload})
    return [item_out(row) for row in saved.get("data") or []]


async def customer_email(ctx: ToolContext, data: dict[str, Any]) -> str | None:
    """The detail call has no customer email; the list row of the same change order has it."""
    filters = {"status": "", "project": str(data.get("project_id") or "")}
    for page in range(5):
        body = await call(
            ctx,
            "change-orders/get-list",
            {"page": page, "limit": 100, "type": data.get("type") or "co", "ignore_filter": 1, "filter": filters},
        )
        rows = (body.get("data") or {}).get("changeOrders") or []
        for row in rows:
            if str(row.get("change_order_id")) == str(data.get("change_order_id")):
                return plain(row.get("email"))
        if len(rows) < 100:
            break
    return None
