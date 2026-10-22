"""Add estimate items: appends priced line items to an estimate (estimate/{id}/add-items)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    LINE_ITEM,
    call,
    dollars,
    item_in,
    item_out,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "estimate_id": {"type": "string", "minLength": 1, "description": "From list_estimates or create_estimate."},
        "items": {"type": "array", "minItems": 1, "maxItems": 100, "items": LINE_ITEM},
        "section_id": {"type": "string", "description": "From get_estimate. Default: the first section."},
    },
    "required": ["estimate_id", "items"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "estimate_id": "1616575",
    "added": [
        {
            "item_id": "30109601",
            "name": "Shaker pantry cabinet, 24 in",
            "type": "material",
            "quantity": 2,
            "unit": "ea",
            "unit_cost": 420.0,
            "markup_percent": 20.0,
            "total": 1008.0,
            "cost_code": None,
            "description": "White painted finish",
            "section": None,
        }
    ],
    "total": 1338.0,
}


async def add_items(ctx: ToolContext, estimate_id: str, items: list[dict[str, Any]], section: str | None) -> list[Any]:
    """Appends items after the ones already there; returns them as the app saved them."""
    current = (await call(ctx, f"estimate/{estimate_id}/get-items", {})).get("data") or {}
    sections = current.get("sections") or []
    if section and not any(str(s.get("section_id")) == section for s in sections):
        raise ToolError("No such section on this estimate; get_estimate lists them.", ErrorCode.INVALID_INPUT)
    section_id = int(section) if section else (sections[0]["section_id"] if sections else None)
    if section_id is None:
        raise ToolError("This estimate has no section to add items to.", ErrorCode.TARGET_ERROR)
    start = len(current.get("items") or [])
    payload = [item_in(item, section_id, start + i + 1, "estimate_item_no") for i, item in enumerate(items)]
    saved = await call(ctx, f"estimate/{estimate_id}/add-items", {"estimate_id": estimate_id, "items": payload})
    return [item_out(row) for row in saved.get("data") or []]


@tool(
    name="add_estimate_items",
    title="Add estimate items",
    access="write",
    description="Adds priced line items to an existing estimate.",
    details=(
        "Adds line items at the end of an estimate section (the first one unless section_id says otherwise). "
        "Each item has a name, a type (material, labor, equipment, subcontractor, other), quantity, unit, your "
        "unit cost in dollars and a markup percent. Contractor Foreman computes the totals. cost_code_id comes "
        "from list_cost_codes. Returns the saved items and the new estimate total."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /estimates/{estimate_id}/items",
    example_response=EXAMPLE_RESPONSE,
)
async def add_estimate_items(ctx: ToolContext, args: dict[str, Any]) -> Any:
    estimate_id = str(args["estimate_id"])
    added = await add_items(ctx, estimate_id, args["items"], args.get("section_id"))
    detail = (await call(ctx, f"estimate/{estimate_id}/detail", {})).get("data") or {}
    return {"estimate_id": estimate_id, "added": added, "total": dollars(detail.get("total"))}
