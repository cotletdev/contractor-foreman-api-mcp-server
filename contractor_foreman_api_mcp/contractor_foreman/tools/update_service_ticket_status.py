"""Update service ticket status: the status field on a service ticket."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, status_id
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import TICKET_KEYS, TICKET_STATUSES
from contractor_foreman_api_mcp.contractor_foreman.tools.get_service_ticket import EXAMPLE_TICKET, read_ticket
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "service_ticket_id": {"type": "integer", "description": "service_ticket_id from list_service_tickets."},
        "status": {"type": "string", "enum": TICKET_STATUSES},
    },
    "required": ["service_ticket_id", "status"],
    "additionalProperties": False,
}


@tool(
    name="update_service_ticket_status",
    title="Update service ticket status",
    access="write",
    confirm=False,
    description="Moves a service ticket to scheduled, en route, checked in, completed, closed and so on.",
    details=(
        "Sets the status of a Contractor Foreman service ticket as the status field on its page does: "
        "unscheduled, scheduled, en_route, checked_in, requires_followup, canceled, completed or closed. The "
        "app's own en-route and completion emails to the customer are separate buttons and are not sent. Completed "
        "moves the service date to today, as the app does. "
        "Returns the ticket as saved."
    ),
    input_schema=INPUT_SCHEMA,
    route="PUT /service-tickets/{service_ticket_id}/status",
    example_response={**EXAMPLE_TICKET, "status": "Completed"},
)
async def update_service_ticket_status(ctx: ToolContext, args: dict[str, Any]) -> Any:
    wanted = await status_id(ctx, "service_ticket_job_status", TICKET_KEYS[args["status"]])
    await call(
        ctx,
        "service-ticket/update-service-ticket-details",
        {"service_ticket_id": args["service_ticket_id"], "job_status": wanted},
    )
    return await read_ticket(ctx, args["service_ticket_id"])
