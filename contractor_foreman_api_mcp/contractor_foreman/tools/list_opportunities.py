"""List opportunities: the Opportunities pipeline (deals before they become projects)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    CURSOR_SCHEMA,
    LIMIT_SCHEMA,
    call,
    date_format,
    next_cursor,
    page,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_opportunities import EXAMPLE_OPPORTUNITY, opportunity_out
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "search": {"type": "string", "description": "Words in the name, number or customer."},
        "limit": LIMIT_SCHEMA,
        "cursor": CURSOR_SCHEMA,
    },
    "required": [],
    "additionalProperties": False,
}


@tool(
    name="list_opportunities",
    title="List opportunities",
    access="read",
    confirm=False,
    description="Sales opportunities with customer, stage, score, budget and expected sale date.",
    details=(
        "Reads the Contractor Foreman Opportunities list: deals for a customer before they turn into a project, at "
        "every stage, with number, name, stage (received, pending, qualifying, qualified, quoted, awarded, lost), "
        "score 1 to 5, budget in the account currency, estimated sales date and who it is assigned to. Search by "
        "name, number or customer."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /opportunities",
    example_response={"opportunities": [EXAMPLE_OPPORTUNITY], "next_cursor": None},
)
async def list_opportunities(ctx: ToolContext, args: dict[str, Any]) -> Any:
    start, size = page(args)
    payload: dict[str, Any] = {"start": start, "limit": size, "ignore_filter": 1}
    if args.get("search"):
        payload["search"] = args["search"].strip()
    body = await call(ctx, "opportunities/get-list", payload)
    found = [r for r in body.get("projects") or [] if isinstance(r, dict)]
    fmt = await date_format(ctx)
    return {
        "opportunities": [opportunity_out(r, fmt) for r in found],
        "next_cursor": next_cursor(start, size, len(found)),
    }
