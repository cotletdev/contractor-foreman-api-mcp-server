"""List cost items: the Cost Items Database (materials, labor, equipment, subcontracts, other) with prices."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import call, dollars, number
from contractor_foreman_api_mcp.core.helpers import limit, page_cursor
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# cidb-items moduleKey per type; item_mixed is all of them.
_MODULE_KEYS = {"material": "item_material", "labor": "item_labour", "equipment": "item_equipment"}
_ID_KEYS = ("material_id", "labor_id", "equipment_id", "contractor_id", "other_item_id")
_TYPES = {"Material": "material", "Labor": "labor", "Equipment": "equipment", "Subcontractor": "subcontractor"}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["material", "labor", "equipment", "subcontractor", "other"]},
        "search": {"type": "string", "description": "Matches the item name."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "items": [
        {
            "cost_item_id": "1985116",
            "name": "Carpenter",
            "type": "labor",
            "unit": "hr",
            "unit_cost": 31.25,
            "markup_percent": None,
            "cost_code_id": None,
            "cost_code": None,
            "sku": None,
            "notes": None,
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_cost_items",
    title="List cost items",
    access="read",
    description="Saved cost items with unit, unit cost and markup, to price estimate and change order lines.",
    details=(
        "The Cost Items Database: name, type, unit, your unit cost in dollars, default markup, cost code, SKU "
        "and notes. Use the values as line items in create_estimate, add_estimate_items or "
        "create_change_order. Filter by type or a name search. Subcontractor and other items are picked out of "
        "each page of all items, so such a page can hold fewer than limit. Keep the cursor going until "
        "next_cursor is null."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /cost-items",
    example_response=EXAMPLE_RESPONSE,
)
async def list_cost_items(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 50, 100)
    page = page_cursor(args.get("cursor"))
    kind = args.get("type")
    payload: dict[str, Any] = {
        "status": 0,
        "orderBy": "name",
        "page": page - 1,
        "limit": size,
        "moduleKey": _MODULE_KEYS.get(kind or "", "item_mixed"),
    }
    if args.get("search"):
        payload["filter"] = {"name": args["search"]}
    rows = (await call(ctx, "cidb-items", payload)).get("data") or []
    items = []
    for row in rows:
        row_type = _TYPES.get(str(row.get("item_type")), "other")
        if kind and row_type != kind:
            continue
        ident = row.get("id") or next(
            (
                row[key]
                for key in ("material_id", "labor_id", "equipment_id", "contractor_id", "other_item_id")
                if row.get(key)
            ),
            None,
        )
        items.append(
            {
                "cost_item_id": str(ident) if ident else None,
                "name": row.get("name"),
                "type": row_type,
                "unit": row.get("unit") or None,
                "unit_cost": dollars(row.get("unit_cost")),
                "markup_percent": float(row["markup"]) if row.get("markup") not in (None, "") else None,
                "cost_code_id": str(row["cost_code_id"]) if number(row.get("cost_code_id")) else None,
                "cost_code": row.get("cost_code_name") or None,
                "sku": row.get("sku") or None,
                "notes": row.get("notes") or None,
            }
        )
    return {"items": items, "next_cursor": str(page + 1) if len(rows) == size else None}
