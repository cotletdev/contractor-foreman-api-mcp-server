"""List service tickets: Service Tickets for service calls and repairs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import ticket_out
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
    "service_ticket_id": 562743,
    "number": "3",
    "title": "Kitchen sink drain backing up",
    "description": "Customer reports slow drain and gurgling under the kitchen sink.",
    "status": "Scheduled",
    "customer_id": 6819060,
    "customer": "Barry Sizemore (Burger Palace)",
    "project_id": None,
    "project": None,
    "service_date": "2026-10-24",
    "service_time": "09:00 AM",
    "technicians": None,
}


@tool(
    name="list_service_tickets",
    title="List service tickets",
    access="read",
    confirm=False,
    description="Service tickets with customer, status, service date and time and technicians.",
    details=(
        "Reads the Contractor Foreman Service Tickets list, newest first: ticket number, title, description, "
        "status (Unscheduled, Scheduled, En Route, Checked-In, Completed ...), customer, project, service "
        "date and time and the assigned technicians. Filter by project or search."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /service-tickets",
    example_response={"service_tickets": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_service_tickets(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "service-ticket", None, ticket_out)
    return {"service_tickets": found, "next_cursor": cursor}
