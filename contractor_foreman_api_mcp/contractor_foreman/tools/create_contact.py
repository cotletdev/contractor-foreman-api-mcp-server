"""Create contact: Directory, Add, for a customer, employee, contractor, vendor or misc contact."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CONTACT_TYPES
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_directory import ADDRESS_PROPS, add_directory
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": list(CONTACT_TYPES), "description": "What kind of contact."},
        "first_name": {"type": "string", "maxLength": 100},
        "last_name": {"type": "string", "maxLength": 100},
        "company_name": {"type": "string", "maxLength": 200, "description": "Required for contractors and vendors."},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string", "maxLength": 30},
        "cell": {"type": "string", "maxLength": 30},
        **ADDRESS_PROPS,
    },
    "required": ["type"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "contact_id": 6819139,
    "type": "vendor",
    "name": "Dana Whitfield",
    "company": "Triangle Lumber Supply",
    "display_name": "Dana Whitfield (Triangle Lumber Supply)",
    "title": None,
    "email": None,
    "phone": "(919) 555-0142",
    "cell": None,
    "address": {"address1": "2100 Capital Blvd", "address2": None, "city": "Raleigh", "state": "NC", "zip": "27604"},
}


@tool(
    name="create_contact",
    title="Create contact",
    access="write",
    confirm=False,
    description="Adds a customer, employee, contractor, vendor or misc contact to the Directory.",
    details=(
        "Creates a Contractor Foreman Directory record as the Add drawer does. Employees need a first and last "
        "name, contractors and vendors a company name, the others a name or a company. The record gets no app "
        "access and nobody is invited or emailed. Giving an employee a login stays a step in the app. Returns "
        "the new contact_id."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /contacts",
    example_response=EXAMPLE_RESPONSE,
)
async def create_contact(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fields = {k: v for k, v in args.items() if k != "type"}
    return await add_directory(ctx, CONTACT_TYPES[args["type"]], fields)
