"""Get daily log: one log with its People, Materials and Equipment tabs (`daily-log/{id}` and its `get-*` calls)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._daily_logs import EXAMPLE_LOG, read_log
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

LOG_ID = {"type": "string", "pattern": "^[0-9]+$", "description": "daily_log_id from list_daily_logs."}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"daily_log_id": LOG_ID},
    "required": ["daily_log_id"],
    "additionalProperties": False,
}


@tool(
    name="get_daily_log",
    title="Get daily log",
    access="read",
    description="One daily log: work notes, people and visitors, materials, equipment, weather and delays.",
    details=(
        "Returns one daily log in full: the work performed, crew notes and employees on site, visitors, "
        "materials, equipment used with hours, the weather Contractor Foreman recorded for the date and the "
        "address (temperatures in both scales, the day's conditions), your weather notes and any weather or "
        "schedule delay. Read only."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /daily-logs/{daily_log_id}",
    example_response=EXAMPLE_LOG,
)
async def get_daily_log(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_log(ctx, args["daily_log_id"])
