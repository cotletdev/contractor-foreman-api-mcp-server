"""Create inspection: Inspections, Add, then agency, inspector and notes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    app_date,
    call,
    created_id,
    date_format,
    status_id,
)
from contractor_foreman_api_mcp.contractor_foreman.tools.get_inspection import EXAMPLE_INSPECTION, read_inspection
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

AGENCIES = {"internal": "inspection_internal", "county": "inspection_country", "city": "inspection_city"}
AGENCIES["independent_agency"] = "inspection_independant_agency"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "integer", "description": "The project being inspected."},
        "type": {"type": "string", "minLength": 1, "maxLength": 200, "description": "e.g. Framing, Rough Electrical."},
        "date": {**DATE_SCHEMA, "description": "Inspection day, YYYY-MM-DD. Default: today."},
        "agency": {"type": "string", "enum": list(AGENCIES)},
        "inspected_by": {"type": "string", "maxLength": 200, "description": "Inspector or office."},
        "notes": {"type": "string", "maxLength": 5000},
    },
    "required": ["project_id", "type"],
    "additionalProperties": False,
}


@tool(
    name="create_inspection",
    title="Create inspection",
    access="write",
    confirm=False,
    description="Logs an inspection on a project with type, date, agency, inspector and notes.",
    details=(
        "Creates a Contractor Foreman inspection in Draft status on a project: inspection type, day, agency "
        "(internal, county, city or independent agency), inspector and notes. record_inspection_result sets "
        "pass, fail or re-inspect afterwards. Nobody is notified. Returns the saved inspection."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /inspections",
    example_response=EXAMPLE_INSPECTION,
)
async def create_inspection(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fmt = await date_format(ctx)
    payload: dict[str, Any] = {
        "project_id": args["project_id"],
        "inspection_type": args["type"].strip(),
        "access_to_custom_fields": 0,
    }
    if args.get("date"):
        payload["inspection_date"] = app_date(args["date"], fmt)
    inspection_id = created_id(await call(ctx, "inspections/add-inspection-data", payload), "inspection_id")
    # The add form keeps type and date only; agency, inspector and notes are field edits on the record.
    update: dict[str, Any] = {k: args[k].strip() for k in ("inspected_by", "notes") if args.get(k)}
    if args.get("agency"):
        update["inspection_agency"] = await status_id(ctx, "inspection_agency", AGENCIES[args["agency"]])
    if update:
        await call(ctx, f"inspections/{inspection_id}/update-inspection-detail", update)
    return await read_inspection(ctx, inspection_id)
