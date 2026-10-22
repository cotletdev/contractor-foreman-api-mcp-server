"""Record inspection result: the status field on an inspection (pass, fail, re-inspect)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, status_id
from contractor_foreman_api_mcp.contractor_foreman.tools.get_inspection import EXAMPLE_INSPECTION, read_inspection
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

RESULTS = {"draft": "inspection_draft", "pass": "inspection_pass", "fail": "inspection_fail"}
RESULTS["re_inspect"] = "inspection_re_inspect"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "inspection_id": {"type": "integer", "description": "inspection_id from list_inspections."},
        "result": {"type": "string", "enum": list(RESULTS)},
        "notes": {"type": "string", "maxLength": 5000, "description": "Replaces the inspection's notes."},
    },
    "required": ["inspection_id", "result"],
    "additionalProperties": False,
}


@tool(
    name="record_inspection_result",
    title="Record inspection result",
    access="write",
    confirm=False,
    description="Marks an inspection passed, failed or to re-inspect, optionally with notes.",
    details=(
        "Sets the status of a Contractor Foreman inspection to pass, fail, re_inspect or back to draft, as the "
        "status field on its page does, and optionally replaces its notes (corrections the inspector asked for). "
        "Nobody is notified. Returns the inspection as saved."
    ),
    input_schema=INPUT_SCHEMA,
    route="PUT /inspections/{inspection_id}/result",
    example_response={**EXAMPLE_INSPECTION, "status": "Pass"},
)
async def record_inspection_result(ctx: ToolContext, args: dict[str, Any]) -> Any:
    update: dict[str, Any] = {"inspection_status": await status_id(ctx, "inspection_status", RESULTS[args["result"]])}
    if args.get("notes"):
        update["notes"] = args["notes"].strip()
    await call(ctx, f"inspections/{args['inspection_id']}/update-inspection-detail", update)
    return await read_inspection(ctx, args["inspection_id"])
