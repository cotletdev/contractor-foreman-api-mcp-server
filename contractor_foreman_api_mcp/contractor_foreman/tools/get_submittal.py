"""Get submittal: one submittal with its items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, iso, num, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import submittal_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"submittal_id": {"type": "integer", "description": "submittal_id from list_submittals."}},
    "required": ["submittal_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "submittal_id": 134560,
    "number": "3",
    "title": "Vent Hoods and Filtration",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "status": "Draft",
    "date_received": "2024-01-01",
    "due_date": "2024-01-15",
    "assigned_to": None,
    "approved_by": None,
    "plan_sheet": "M2.32",
    "specification": "14.02.32",
    "items": [
        {
            "item_id": 412233,
            "description": "Exhaust hood, 12 ft stainless",
            "manufacturer": None,
            "status": None,
            "date_sent_back": None,
        }
    ],
}


@tool(
    name="get_submittal",
    title="Get submittal",
    access="read",
    confirm=False,
    description="One submittal with plan sheet, specification section, status, dates and its items.",
    details=(
        "Reads one Contractor Foreman submittal by submittal_id: what list_submittals gives plus the plan sheet "
        "and specification section and each submitted item with manufacturer, status and the date it was sent "
        "back."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /submittals/{submittal_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_submittal(ctx: ToolContext, args: dict[str, Any]) -> Any:
    body = await call(ctx, f"submittal/{args['submittal_id']}/submittal-detail")
    data = body.get("data") or {}
    row = data.get("submittal_data") or {}
    if not row.get("submittal_id"):
        raise ToolError("Contractor Foreman did not find that submittal.", ErrorCode.TARGET_ERROR)
    fmt = await date_format(ctx)
    out = submittal_out(row, fmt)
    out["plan_sheet"] = text(row.get("plan_sheet_number"))
    out["specification"] = text(row.get("specifications"))
    items = await call(ctx, f"submittal/{args['submittal_id']}/submittal-items")
    found = items.get("data")
    found = found.get("items") if isinstance(found, dict) else found
    out["items"] = [
        {
            "item_id": num(i.get("item_id") or i.get("submittal_item_id")),
            "description": text(i.get("title") or i.get("description") or i.get("subject")),
            "manufacturer": text(i.get("manufacturer")),
            "status": text(i.get("status_name")),
            "date_sent_back": iso(i.get("date_sent_back"), fmt),
        }
        for i in found or []
        if isinstance(i, dict)
    ]
    return out
