"""Delete estimate: removes one estimate and its items (common/delete, module estimates)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import delete_record
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"estimate_id": {"type": "string", "minLength": 1, "description": "From list_estimates."}},
    "required": ["estimate_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"estimate_id": "1616575", "deleted": True}


@tool(
    name="delete_estimate",
    title="Delete estimate",
    access="write",
    description="Deletes an estimate for good.",
    details=(
        "Deletes the estimate and its line items, as Delete in the estimate's menu does. Records made from "
        "it (projects, change orders, invoices) stay. It cannot be undone. To keep the history, use "
        "update_estimate with status lost instead."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /estimates/{estimate_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def delete_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    await delete_record(ctx, "estimates", int(args["estimate_id"]))
    return {"estimate_id": str(args["estimate_id"]), "deleted": True}
