"""Get estimate: one estimate with its customer, terms, sections and line items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    ESTIMATE_STATUSES,
    call,
    dollars,
    iso,
    item_out,
    key_of,
    number,
    plain,
)
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"estimate_id": {"type": "string", "minLength": 1, "description": "From list_estimates."}},
    "required": ["estimate_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "estimate_id": "1616575",
    "number": "5",
    "title": "Pantry Cabinet Addition",
    "status": "estimating",
    "status_name": "Estimating",
    "project_id": "1678167",
    "project_name": "Kitchen Upgrade",
    "customer": {
        "customer_id": "6819060",
        "name": "Dana Whitfield",
        "company": "Whitfield Homes",
        "email": "dana@example.com",
        "phone": "(919) 555-0142",
        "address": "218 Maple St, Raleigh, NC 27601",
    },
    "estimate_date": "2026-10-21",
    "expire_date": "2026-11-20",
    "billing": "unit",
    "description": "Remove two upper cabinets and install two shaker pantry units.",
    "inclusions": None,
    "exclusions": None,
    "terms": "Please review the following terms prior to work beginning.",
    "subtotal": 1170.0,
    "markup_total": 168.0,
    "tax_rate_percent": 0.0,
    "total": 1338.0,
    "items": [
        {
            "item_id": "30109600",
            "name": "Cabinet removal labor",
            "type": "labor",
            "quantity": 6,
            "unit": "Hrs",
            "unit_cost": 55.0,
            "markup_percent": None,
            "total": 330.0,
            "cost_code": None,
            "description": None,
            "section": "Item",
        }
    ],
    "sections": [{"section_id": "5788803", "name": "Item", "total": 1338.0}],
}


def _text(value: Any) -> str | None:
    return plain(value)


@tool(
    name="get_estimate",
    title="Get estimate",
    access="read",
    description="One estimate with customer, dates, terms, totals and every line item.",
    details=(
        "Everything on one estimate: status, project, customer contact, estimate and expiry dates, billing "
        "type, description, inclusions, exclusions, terms, totals in dollars and the line items by section "
        "(type, quantity, unit, unit cost, markup, total, cost code). section_id is what add_estimate_items "
        "takes to put new items in a section."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /estimates/{estimate_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    estimate_id = args["estimate_id"]
    data = (await call(ctx, f"estimate/{estimate_id}/detail", {})).get("data") or {}
    items = (await call(ctx, f"estimate/{estimate_id}/get-items", {})).get("data") or {}
    address = ", ".join(
        part
        for part in (
            _text(data.get("customer_address1")),
            _text(data.get("cust_city")),
            " ".join(p for p in (_text(data.get("cust_state")), _text(data.get("cust_zip"))) if p) or None,
        )
        if part
    )
    rows = items.get("items") or []
    subtotal = sum(float(row.get("no_mu_total") or 0) for row in rows)
    markup = sum(float(row.get("markup_amount") or 0) for row in rows)
    return {
        "estimate_id": str(data.get("estimate_id")),
        "number": data.get("company_estimate_id"),
        "title": data.get("title"),
        "status": key_of(ESTIMATE_STATUSES, data.get("approval_type_key")),
        "status_name": data.get("approval_type_name"),
        "project_id": str(data["project_id"]) if number(data.get("project_id")) else None,
        "project_name": data.get("project_name"),
        "customer": {
            "customer_id": str(data["customer_id"]) if number(data.get("customer_id")) else None,
            "name": _text(data.get("customer_name_only")),
            "company": _text(data.get("customer_company")),
            "email": _text(data.get("customer_email")),
            "phone": _text(data.get("customer_cell")) or _text(data.get("customer_phone")),
            "address": address or None,
        },
        "estimate_date": iso(data.get("estimate_date")),
        "expire_date": iso(data.get("expire_date")),
        "billing": data.get("billing_option"),
        "description": _text(data.get("description")),
        "inclusions": _text(data.get("inclusion")),
        "exclusions": _text(data.get("exclusion")),
        "terms": _text(data.get("terms")),
        "subtotal": dollars(subtotal),
        "markup_total": dollars(markup),
        "tax_rate_percent": float(data.get("total_tax_rate") or 0),
        "total": dollars(data.get("total")),
        "items": [item_out(row) for row in rows],
        "sections": [
            {
                "section_id": str(section.get("section_id")),
                "name": section.get("section_name"),
                "total": dollars(section.get("section_total")),
            }
            for section in items.get("sections") or []
        ],
    }
