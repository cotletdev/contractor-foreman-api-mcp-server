"""Shapes shared by the bill, expense, purchase order and sub-contract tools (recorded 21.10.2026)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    call,
    date_format,
    iso,
    money,
    next_cursor,
    num,
    page,
    rows,
    text,
    to_cents,
)

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# Item types of the company's cost items (common/get-status-list "company_items").
ITEM_TYPES: dict[str, int] = {"material": 161, "equipment": 162, "labor": 163, "subcontractor": 164, "other": 165}
ITEM_TYPE_NAMES = {v: k for k, v in ITEM_TYPES.items()}

ITEMS_SCHEMA: dict[str, Any] = {
    "type": "array",
    "minItems": 1,
    "maxItems": 50,
    "description": "Line items. The total is the sum of quantity times unit cost.",
    "items": {
        "type": "object",
        "properties": {
            "description": {"type": "string", "minLength": 1, "maxLength": 300},
            "quantity": {"type": "number", "exclusiveMinimum": 0, "default": 1},
            "unit": {"type": "string", "maxLength": 20, "description": "ea, ls, case, hr, sq ft ..."},
            "unit_cost": {"type": "number", "minimum": 0, "description": "In the account currency."},
            "type": {"type": "string", "enum": list(ITEM_TYPES), "default": "material"},
        },
        "required": ["description", "unit_cost"],
        "additionalProperties": False,
    },
}

LIST_PROPS: dict[str, Any] = {
    "project_id": {"type": "integer", "description": "Only this project's records."},
    "search": {"type": "string", "description": "Words to look for."},
}


def items_in(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in items:
        quantity = item.get("quantity") or 1
        unit_cost = to_cents(item["unit_cost"])
        out.append(
            {
                "subject": item["description"].strip(),
                "quantity": quantity,
                "unit": (item.get("unit") or "ea").strip(),
                "unit_cost": str(unit_cost),
                "item_type": ITEM_TYPES[item.get("type") or "material"],
                "total": str(round(unit_cost * quantity)),
            }
        )
    return out


def item_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": num(row.get("item_id")),
        "description": text(row.get("subject")),
        "type": ITEM_TYPE_NAMES.get(num(row.get("item_type")) or 0, text(row.get("item_type_name"))),
        "quantity": row.get("quantity"),
        "unit": text(row.get("unit")),
        "unit_cost": money(row.get("unit_cost")),
        "total": money(row.get("total")),
        "cost_code": text(row.get("cost_code_name")),
    }


async def list_records(
    ctx: ToolContext, args: dict[str, Any], path: str, wrap: str | None, shape: Any
) -> tuple[list[dict[str, Any]], str | None]:
    """One page of a module list with the panel's paging, `filter.project` and `search`."""
    start, size = page(args)
    payload: dict[str, Any] = {"start": start, "limit": size, "ignore_filter": 1}
    if args.get("project_id"):
        payload["filter"] = {"project": str(args["project_id"])}
    if args.get("search"):
        payload["search"] = args["search"].strip()
    body = await call(ctx, path, payload)
    found = [r for r in rows(body, *([wrap] if wrap else [])) if isinstance(r, dict)]
    fmt = await date_format(ctx)
    return [shape(r, fmt) for r in found], next_cursor(start, size, len(found))


def bill_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "bill_id": num(row.get("bill_id")),
        "number": text(row.get("custom_bill_id") or row.get("company_bill_id")),
        "subject": text(row.get("subject")) if str(row.get("subject")) != "0" else None,
        "vendor_id": num(row.get("supplier_id")),
        "vendor": text(row.get("supplier_name")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "bill_date": iso(row.get("order_date"), fmt),
        "due_date": iso(row.get("due_date"), fmt),
        "total": money(row.get("total")),
        "balance_due": money(row.get("due_balance")),
        "status": text(row.get("bill_status_name")),
        "status_id": num(row.get("bill_status")),
        "notes": text(row.get("notes")),
    }


def expense_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "expense_id": num(row.get("expense_id")),
        "name": text(row.get("expense_name")),
        "amount": money(row.get("amount_with_tax") or row.get("amount")),
        "date": iso(row.get("expense_date"), fmt),
        "vendor_id": num(row.get("directory_id")),
        "vendor": text(row.get("vendor_name")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "type": text(row.get("item_type_name")),
        "paid_by": text(row.get("expense_by_name") or row.get("employee")),
        "paid_through": text(row.get("paid_through_name")),
        "billable": bool(num(row.get("is_billable"))),
        "reason": text(row.get("reason")),
    }


def purchase_order_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "purchase_order_id": num(row.get("purchase_order_id")),
        "number": text(row.get("prefix_company_purchase_order_id") or row.get("company_purchase_order_id")),
        "subject": text(row.get("subject")),
        "vendor_id": num(row.get("supplier_id")),
        "vendor": text(row.get("supplier_name")),
        "project_id": num(row.get("pro_id") or row.get("project_id")),
        "project": text(row.get("project_name")),
        "order_date": iso(row.get("order_date"), fmt),
        "delivery_date": iso(row.get("delivery_date"), fmt),
        "total": money(row.get("total")),
        "status": text(row.get("billing_status_name")),
        "ordered_by": text(row.get("order_from_username")),
        "ship_via": text(row.get("ship_via")),
        "terms": text(row.get("term_name")),
        "notes": text(row.get("notes")),
    }


def sub_contract_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "sub_contract_id": num(row.get("sub_contract_id")),
        "agreement_number": text(row.get("prefix_company_sub_contract_id") or row.get("agreement")),
        "subject": text(row.get("subject")),
        "contractor_id": num(row.get("contractor_id")),
        "contractor": text(row.get("contractor_name")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "date": iso(row.get("order_date"), fmt),
        "total": money(row.get("total")),
        "billed": money(row.get("sc_billed_amount")),
        "paid": money(row.get("paid_value")),
        "balance": money(row.get("balance")),
        "retainage_percent": float(row["work_retain"]) if row.get("work_retain") else None,
        "status": text(row.get("response_name")),
        "issued_by": text(row.get("issued_by_username")),
    }
