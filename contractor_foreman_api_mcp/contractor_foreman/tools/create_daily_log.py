"""Create daily log: `daily-log/add` (project, date, arrival time), then the sections in `_daily_logs.write_fields`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._daily_logs import (
    EXAMPLE_LOG,
    WRITE_PROPERTIES,
    read_log,
    write_fields,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import panel, parse_date, time_24
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import PROJECT_ID
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": PROJECT_ID,
        "date": {"type": "string", "format": "date", "description": "Log date."},
        **WRITE_PROPERTIES,
    },
    "required": ["project_id", "date", "notes"],
    "additionalProperties": False,
}


@tool(
    name="create_daily_log",
    title="Create daily log",
    access="write",
    description="New daily log on a project: work notes, people, deliveries, weather notes and delays.",
    details=(
        "Adds a daily log to the project for the date you give (arrival 07:00 unless you say otherwise) and "
        "returns it as get_daily_log shows it. Contractor Foreman records the weather for the date and the "
        "project address itself, and weather_notes sits next to it. notes must not be empty. people takes a "
        "headcount per crew or free text. The log reaches no client or crew and update_daily_log can edit "
        "it, so this tool runs "
        "without asking. One project can have several logs on one date: check list_daily_logs first."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /daily-logs",
    example_response=EXAMPLE_LOG,
)
async def create_daily_log(ctx: ToolContext, args: dict[str, Any]) -> Any:
    if not (args.get("notes") or "").strip():
        raise ToolError("notes must say what was done on site.", ErrorCode.INVALID_INPUT)
    body = await panel(
        ctx,
        "daily-log/add",
        {
            "projectId": args["project_id"],
            "arrivalDate": parse_date(args["date"], "date").isoformat(),
            "arrivalTime": time_24(args.get("arrival_time") or "07:00", "arrival_time"),
            "accessToCustomFields": 0,
        },
    )
    log_id = str((body.get("data") or {}).get("dailyLogId") or "")
    if not log_id:
        raise ToolError("Contractor Foreman did not return the new daily log.", ErrorCode.TARGET_ERROR)
    await write_fields(ctx, log_id, args, skip_arrival=True)
    return await read_log(ctx, log_id)
