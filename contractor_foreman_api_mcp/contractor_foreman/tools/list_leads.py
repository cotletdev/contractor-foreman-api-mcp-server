"""List leads: Directory records of the Lead type, with stage and quality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LEAD_TYPE, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_directory import list_directory
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "search": {"type": "string", "description": "Name, company, email or phone to look for."},
        "limit": LIMIT_SCHEMA,
        "cursor": CURSOR_SCHEMA,
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "leads": [
        {
            "contact_id": 6819148,
            "type": "lead",
            "name": "Megan Cortez",
            "company": None,
            "display_name": "Megan Cortez",
            "title": None,
            "email": None,
            "phone": None,
            "cell": "(919) 555-0187",
            "address": {
                "address1": "412 Oberlin Rd",
                "address2": None,
                "city": "Raleigh",
                "state": "NC",
                "zip": "27605",
            },
            "stage": "received",
            "quality": 3,
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_leads",
    title="List leads",
    access="read",
    confirm=False,
    description="Sales leads with contact details, stage and quality score.",
    details=(
        "Reads the active leads in the Contractor Foreman Directory: name, company, email, phone, address, "
        "stage (received, pending, qualifying, qualified, quoted, awarded, lost) and quality from 1 to 5. "
        "Search by name, company, email or phone. Opportunities (deals tied to a customer) are list_opportunities."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /leads",
    example_response=EXAMPLE_RESPONSE,
)
async def list_leads(ctx: ToolContext, args: dict[str, Any]) -> Any:
    out = await list_directory(ctx, args, [LEAD_TYPE])
    return {"leads": out["contacts"], "next_cursor": out["next_cursor"]}
