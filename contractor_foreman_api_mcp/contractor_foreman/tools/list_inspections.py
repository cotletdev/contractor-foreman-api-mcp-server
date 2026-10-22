"""List inspections: Inspections on projects (city, county, internal)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import inspection_out
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import LIST_PROPS, list_records
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {**LIST_PROPS, "limit": LIMIT_SCHEMA, "cursor": CURSOR_SCHEMA},
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_ROW: dict[str, Any] = {
    "inspection_id": 132543,
    "number": "2",
    "type": "Framing Inspection",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "date": "2026-10-28",
    "time": "07:57 AM",
    "status": "Draft",
    "agency": None,
    "inspected_by": None,
    "permit_number": None,
    "assigned_to": None,
    "notes": None,
}


@tool(
    name="list_inspections",
    title="List inspections",
    access="read",
    confirm=False,
    description="Inspections with project, type, date, result, agency and permit number.",
    details=(
        "Reads the Contractor Foreman Inspections list, newest first: number, inspection type, project, date "
        "and time, status (Draft, Pass, Fail, Re-Inspect), agency, inspector, permit number, assignee and "
        "notes. Filter by project or search."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /inspections",
    example_response={"inspections": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_inspections(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "inspections/get-inspection-list", None, inspection_out)
    return {"inspections": found, "next_cursor": cursor}
