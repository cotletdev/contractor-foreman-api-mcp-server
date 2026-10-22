"""Get inspection: one inspection record."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import inspection_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"inspection_id": {"type": "integer", "description": "inspection_id from list_inspections."}},
    "required": ["inspection_id"],
    "additionalProperties": False,
}

EXAMPLE_INSPECTION: dict[str, Any] = {
    "inspection_id": 132545,
    "number": "3",
    "type": "Rough Electrical",
    "project_id": 1678167,
    "project": "Kitchen Upgrade",
    "date": "2026-10-29",
    "time": "08:20 AM",
    "status": "Draft",
    "agency": "City",
    "inspected_by": "Raleigh Building Inspections",
    "permit_number": None,
    "assigned_to": None,
    "notes": "Kitchen circuits and pantry switch relocation",
}


async def read_inspection(ctx: ToolContext, inspection_id: int) -> dict[str, Any]:
    row = first_record(await call(ctx, f"inspections/{inspection_id}/inspection-details"))
    if not row.get("inspection_id"):
        raise ToolError("Contractor Foreman did not find that inspection.", ErrorCode.TARGET_ERROR)
    return inspection_out(row, await date_format(ctx))


@tool(
    name="get_inspection",
    title="Get inspection",
    access="read",
    confirm=False,
    description="One inspection with type, project, date, result, agency, inspector and notes.",
    details="Reads one Contractor Foreman inspection by inspection_id, with the same fields as list_inspections.",
    input_schema=INPUT_SCHEMA,
    route="GET /inspections/{inspection_id}",
    example_response=EXAMPLE_INSPECTION,
)
async def get_inspection(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_inspection(ctx, args["inspection_id"])
