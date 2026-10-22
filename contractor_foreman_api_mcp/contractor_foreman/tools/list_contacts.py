"""List contacts: the Directory (customers, employees, contractors, vendors, misc contacts)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CONTACT_TYPES, CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_directory import list_directory
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": list(CONTACT_TYPES),
            "description": "Only this kind of contact. Left out: all of them, leads excluded.",
        },
        "search": {"type": "string", "description": "Name, company, email or phone to look for."},
        "limit": LIMIT_SCHEMA,
        "cursor": CURSOR_SCHEMA,
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "contacts": [
        {
            "contact_id": 6819139,
            "type": "vendor",
            "name": "Dana Whitfield",
            "company": "Triangle Lumber Supply",
            "display_name": "Dana Whitfield (Triangle Lumber Supply)",
            "title": None,
            "email": "dana@trianglelumber.example",
            "phone": "(919) 555-0142",
            "cell": None,
            "address": {
                "address1": "2100 Capital Blvd",
                "address2": None,
                "city": "Raleigh",
                "state": "NC",
                "zip": "27604",
            },
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_contacts",
    title="List contacts",
    access="read",
    confirm=False,
    description="Customers, employees, contractors, vendors and misc contacts from the Directory.",
    details=(
        "Reads the Contractor Foreman Directory: active contacts with their type, name, company, title, email, "
        "phone, cell and address. Filter by type or search by name, company, email or phone. "
        "contact_id is the id other tools ask for as customer_id, vendor_id, contractor_id or employee_id. "
        "Leads have their own tool, list_leads."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /contacts",
    example_response=EXAMPLE_RESPONSE,
)
async def list_contacts(ctx: ToolContext, args: dict[str, Any]) -> Any:
    kind = args.get("type")
    types = [CONTACT_TYPES[kind]] if kind else [1, *CONTACT_TYPES.values()]
    if kind == "employee":
        types = [1, 2]
    return await list_directory(ctx, args, types)
