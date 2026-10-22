"""Remove estimate items: deletes line items from an estimate (estimate/{id}/delete-items)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import call, dollars
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "estimate_id": {"type": "string", "minLength": 1, "description": "From list_estimates."},
        "item_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 100,
            "items": {"type": "string"},
            "description": "item_id values from get_estimate.",
        },
    },
    "required": ["estimate_id", "item_ids"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"estimate_id": "1616575", "removed": ["30109600"], "total": 1008.0}


@tool(
    name="remove_estimate_items",
    title="Remove estimate items",
    access="write",
    description="Deletes line items from an estimate.",
    details=(
        "Deletes the given line items (item_id from get_estimate) and returns the new estimate total. An "
        "item_id that is not on the estimate stops the call before anything is deleted. The app "
        "refuses while the estimate is pending_approval, approved or completed: set it back to estimating "
        "with update_estimate first."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /estimates/{estimate_id}/items",
    example_response=EXAMPLE_RESPONSE,
)
async def remove_estimate_items(ctx: ToolContext, args: dict[str, Any]) -> Any:
    estimate_id = str(args["estimate_id"])
    current = (await call(ctx, f"estimate/{estimate_id}/get-items", {})).get("data") or {}
    known = {str(item.get("item_id")) for item in current.get("items") or []}
    if missing := [item for item in args["item_ids"] if str(item) not in known]:
        raise ToolError(f"Not on this estimate: {', '.join(missing)}.", ErrorCode.INVALID_INPUT)
    ids = [int(item) for item in args["item_ids"]]
    await call(
        ctx,
        f"estimate/{estimate_id}/delete-items",
        {"delete_multiple_item": 1, "multiple_item_id": ids, "estimate_id": estimate_id},
    )
    detail = (await call(ctx, f"estimate/{estimate_id}/detail", {})).get("data") or {}
    return {"estimate_id": estimate_id, "removed": [str(item) for item in ids], "total": dollars(detail.get("total"))}
