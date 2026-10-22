"""Get RFI: one request for information."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record, statuses
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import RFI_TYPE, rfi_out
from contractor_foreman_api_mcp.contractor_foreman.tools.list_rfis import EXAMPLE_RFI
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"rfi_id": {"type": "integer", "description": "rfi_id from list_rfis."}},
    "required": ["rfi_id"],
    "additionalProperties": False,
}


async def read_rfi(ctx: ToolContext, rfi_id: int) -> dict[str, Any]:
    row = first_record(await call(ctx, f"rfi/{rfi_id}"))
    if not row.get("correspondence_id") or row.get("type") != RFI_TYPE:
        raise ToolError("Contractor Foreman did not find that RFI.", ErrorCode.TARGET_ERROR)
    names = {r["id"]: r["name"] for r in await statuses(ctx, "correspondence_rfi")}
    return rfi_out(row, await date_format(ctx), names)


@tool(
    name="get_rfi",
    title="Get RFI",
    access="read",
    confirm=False,
    description="One RFI with its question, dates, answer and status.",
    details="Reads one Contractor Foreman RFI by rfi_id, with the same fields as list_rfis.",
    input_schema=INPUT_SCHEMA,
    route="GET /rfis/{rfi_id}",
    example_response=EXAMPLE_RFI,
)
async def get_rfi(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_rfi(ctx, args["rfi_id"])
