"""List daily logs: the Daily Logs list (`daily-log`, camelCase filter, `start`/`limit`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import (
    compact,
    iso,
    number,
    panel,
    parse_date,
    text,
)
from contractor_foreman_api_mcp.core.helpers import limit
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "pattern": "^[0-9]+$", "description": "Only logs of this project."},
        "from": {"type": "string", "format": "date", "description": "First log date."},
        "to": {"type": "string", "format": "date", "description": "Last log date."},
        "search": {"type": "string", "description": "Text to match, as the search box of the Daily Logs list."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "daily_logs": [
        {
            "daily_log_id": "2021965",
            "date": "2026-10-20",
            "arrival_time": "07:00 AM",
            "project_name": "Speedway - Tenant Fit Out",
            "created_by": "Michael Howard",
            "status": None,
        }
    ],
    "total": 1,
    "next_cursor": None,
}


@tool(
    name="list_daily_logs",
    title="List daily logs",
    access="read",
    description="Daily logs by date, optionally for one project and a date range.",
    details=(
        "Returns daily logs in the order of the Daily Logs list, with date, arrival time, project and who "
        "wrote them, and total, the count of logs that match. Filter by project and by from/to dates (both "
        "inclusive). get_daily_log gives one log in "
        "full: notes, people, materials, equipment and the weather. Pages hold up to 100 logs; pass "
        "next_cursor back as cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /daily-logs",
    example_response=EXAMPLE_RESPONSE,
)
async def list_daily_logs(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 30, 100)
    cursor = args.get("cursor")
    start = int(cursor) if cursor and cursor.isdigit() else 0
    log_filter = compact(
        {
            "projectId": args.get("project_id"),
            "startDate": parse_date(args["from"], "from").isoformat() if args.get("from") else None,
            "endDate": parse_date(args["to"], "to").isoformat() if args.get("to") else None,
        }
    )
    payload: dict[str, Any] = {"start": start, "limit": size, "ignoreFilter": 1}
    if log_filter:
        payload["filter"] = log_filter
    if args.get("search"):
        payload["search"] = args["search"]
    body = await panel(ctx, "daily-log", payload)
    rows = body.get("data") or []
    total = int(number(body.get("totalRecords"))) if body.get("totalRecords") is not None else None
    logs = [
        {
            "daily_log_id": str(row.get("log_id")),
            "date": iso(row.get("arrival_date")),
            "arrival_time": text(row.get("arrival_time")),
            "project_name": text(row.get("project_name")),
            "created_by": text(row.get("employee")),
            "status": text(row.get("job_status_name")),
        }
        for row in rows
    ]
    return {"daily_logs": logs, "total": total, "next_cursor": str(start + size) if len(rows) == size else None}
