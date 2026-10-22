"""Get contact: one Directory record (customer, employee, contractor, vendor, misc contact or lead)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, iso, num, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_directory import contact_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"contact_id": {"type": "integer", "description": "contact_id from list_contacts or list_leads."}},
    "required": ["contact_id"],
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
    "phone2": None,
    "fax": None,
    "website": None,
    "status": "Active",
    "services": None,
    "tags": None,
    "default_terms": None,
    "referral_source": None,
    "added_on": "2026-10-21",
    "additional_contacts": [],
}


@tool(
    name="get_contact",
    title="Get contact",
    access="read",
    confirm=False,
    description="One Directory record in full: contact details, status, services, terms and additional contacts.",
    details=(
        "Reads one Contractor Foreman Directory record by contact_id: everything list_contacts gives plus a second "
        "phone, fax, website, status, services, tags, default payment terms, referral source, the date it was "
        "added and the additional contacts kept under it. For leads also stage and quality. Login details, "
        "wages and personal ids of employees are left out."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /contacts/{contact_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_contact(ctx: ToolContext, args: dict[str, Any]) -> Any:
    body = await call(ctx, "directory/get-directory-details", {"directoryId": args["contact_id"]})
    row = body.get("data") or {}
    if not isinstance(row, dict) or not row.get("user_id"):
        raise ToolError("Contractor Foreman did not find that contact.", ErrorCode.TARGET_ERROR)
    fmt = await date_format(ctx)
    out = contact_out(row)
    out.update(
        {
            "phone2": text(row.get("phone2")),
            "fax": text(row.get("fax")),
            "website": text(row.get("website")),
            "status": text(row.get("status_name")),
            "services": text(row.get("services")),
            "tags": text(row.get("tags")),
            "default_terms": text(row.get("term_name")),
            "referral_source": text(row.get("referral_source_name")),
            "added_on": iso(row.get("date_added"), fmt),
            "additional_contacts": [
                {
                    "contact_id": num(c.get("contact_id")),
                    "name": text(" ".join(p for p in (c.get("first_name") or "", c.get("last_name") or "") if p)),
                    "title": text(c.get("title")),
                    "email": text(c.get("email")),
                    "phone": text(c.get("phone") or c.get("cell")),
                }
                for c in row.get("contacts") or []
                if isinstance(c, dict)
            ],
        }
    )
    return out
