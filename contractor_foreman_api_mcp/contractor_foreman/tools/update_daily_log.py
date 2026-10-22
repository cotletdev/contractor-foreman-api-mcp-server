"""Update daily log: the Details, People and Materials fields of an existing log (`_daily_logs.write_fields`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._daily_logs import (
    EXAMPLE_LOG,
    WRITE_PROPERTIES,
    read_log,
    write_fields,
)
from contractor_foreman_api_mcp.contractor_foreman.tools.get_daily_log import LOG_ID
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"daily_log_id": LOG_ID, **WRITE_PROPERTIES},
    "required": ["daily_log_id"],
    "additionalProperties": False,
}


@tool(
    name="update_daily_log",
    title="Update daily log",
    access="write",
    description="Change the notes, times, people, deliveries, weather notes or delays of a daily log.",
    details=(
        "Replaces only the fields you pass and returns the log as get_daily_log shows it. Text fields are "
        "replaced, not appended: read the log first to add to its notes. materials_delivered replaces the "
        "material notes. weather_delay, schedule_delay and visitors can mark a delay or a visit but not clear "
        "it. The log date and project do not change. The log reaches no client or crew, so this tool runs "
        "without asking."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /daily-logs/{daily_log_id}",
    example_response=EXAMPLE_LOG,
)
async def update_daily_log(ctx: ToolContext, args: dict[str, Any]) -> Any:
    log_id = args["daily_log_id"]
    if len([key for key in args if key != "daily_log_id"]) == 0:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    await read_log(ctx, log_id)
    await write_fields(ctx, log_id, args)
    return await read_log(ctx, log_id)
