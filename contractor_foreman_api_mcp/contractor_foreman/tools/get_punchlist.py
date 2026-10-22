"""Get punchlist: one punchlist's header (`punchlists/{id}/get-punchlist-detail`). Items: see `_punchlists`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._punchlists import (
    EXAMPLE_PUNCHLIST,
    PUNCHLIST_ID,
    read_punchlist,
)
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"punchlist_id": PUNCHLIST_ID},
    "required": ["punchlist_id"],
    "additionalProperties": False,
}


@tool(
    name="get_punchlist",
    title="Get punchlist",
    access="read",
    description="One punchlist: project, address, customer and how many items are open and completed.",
    details=(
        "Returns one punchlist with its project, the project address and customer, the number of open and "
        "completed items, who made it and when. The items themselves are not returned yet: open the "
        "punchlist in Contractor Foreman to see them. Read only."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /punchlists/{punchlist_id}",
    example_response=EXAMPLE_PUNCHLIST,
)
async def get_punchlist(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_punchlist(ctx, args["punchlist_id"])
