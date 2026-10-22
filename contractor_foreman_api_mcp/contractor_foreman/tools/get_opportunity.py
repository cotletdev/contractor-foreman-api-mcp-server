"""Get opportunity: one opportunity's detail page."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_opportunities import EXAMPLE_OPPORTUNITY, opportunity_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"opportunity_id": {"type": "integer", "description": "opportunity_id from list_opportunities."}},
    "required": ["opportunity_id"],
    "additionalProperties": False,
}


@tool(
    name="get_opportunity",
    title="Get opportunity",
    access="read",
    confirm=False,
    description="One opportunity in full: customer contact, stage, score, budget, notes and last activity.",
    details=(
        "Reads one Contractor Foreman opportunity by opportunity_id: what list_opportunities gives plus the "
        "customer's email and phone, the notes and the subject of the last sales activity."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /opportunities/{opportunity_id}",
    example_response={
        **EXAMPLE_OPPORTUNITY,
        "customer_email": "owner@burgerpalace.example",
        "customer_phone": "(410) 555-1212",
        "notes": None,
        "last_activity": None,
    },
)
async def get_opportunity(ctx: ToolContext, args: dict[str, Any]) -> Any:
    body = await call(
        ctx,
        "opportunities/get-opportunity-detail",
        {"project_id": args["opportunity_id"], "record_type": "opportunity"},
    )
    row = first_record(body)
    if not row.get("id"):
        raise ToolError("Contractor Foreman did not find that opportunity.", ErrorCode.TARGET_ERROR)
    out = opportunity_out(row, await date_format(ctx))
    out["customer_email"] = text(row.get("cust_email"))
    out["customer_phone"] = text(row.get("customer_contact_cell") or row.get("cust_cell") or row.get("customer_phone"))
    out["notes"] = text(row.get("notes"))
    out["last_activity"] = text(row.get("last_activity_subject"))
    return out
