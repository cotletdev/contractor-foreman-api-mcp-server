"""Create lead: Leads, Add, a Directory record of the Lead type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import LEAD_TYPE
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_directory import ADDRESS_PROPS, add_directory
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

STAGES = ["received", "pending", "qualifying", "qualified", "quoted", "awarded", "lost"]

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "first_name": {"type": "string", "maxLength": 100},
        "last_name": {"type": "string", "maxLength": 100},
        "company_name": {"type": "string", "maxLength": 200},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string", "maxLength": 30},
        "cell": {"type": "string", "maxLength": 30},
        **ADDRESS_PROPS,
        "stage": {"type": "string", "enum": STAGES, "default": "received"},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "contact_id": 6819148,
    "type": "lead",
    "name": "Megan Cortez",
    "company": None,
    "display_name": "Megan Cortez",
    "title": None,
    "email": None,
    "phone": None,
    "cell": "(919) 555-0187",
    "address": {"address1": "412 Oberlin Rd", "address2": None, "city": "Raleigh", "state": "NC", "zip": "27605"},
    "stage": "received",
    "quality": 3,
}


@tool(
    name="create_lead",
    title="Create lead",
    access="write",
    confirm=False,
    description="Adds a sales lead with contact details and a pipeline stage.",
    details=(
        "Creates a lead in the Contractor Foreman Directory as the Leads Add drawer does: a name or a company, "
        "contact details, address and the stage (received by default). Nobody is emailed. Returns the new "
        "contact_id, which list_leads and get_contact read."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /leads",
    example_response=EXAMPLE_RESPONSE,
)
async def create_lead(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fields = {k: v for k, v in args.items() if k != "stage"}
    fields["stage"] = f"lead_stage_{args.get('stage') or 'received'}"
    return await add_directory(ctx, LEAD_TYPE, fields)
