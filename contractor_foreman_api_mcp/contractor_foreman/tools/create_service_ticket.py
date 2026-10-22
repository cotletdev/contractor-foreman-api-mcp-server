"""Create service ticket: Service Tickets, Add, then the schedule fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import DATE_SCHEMA, call, created_id, status_id
from contractor_foreman_api_mcp.contractor_foreman.tools.get_service_ticket import EXAMPLE_TICKET, read_ticket
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "customer_id": {"type": "integer", "description": "A customer's contact_id (list_contacts type customer)."},
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "description": {"type": "string", "maxLength": 5000, "description": "What the customer reported."},
        "project_id": {
            "type": "integer",
            "description": "Links the ticket to a project. The service address is then the project's.",
        },
        "service_date": {
            **DATE_SCHEMA,
            "description": "Planned visit, YYYY-MM-DD. The ticket is then Scheduled.",
        },
        "service_time": {
            "type": "string",
            "pattern": "^([01][0-9]|2[0-3]):[0-5][0-9]$",
            "description": "Planned time on the 24-hour clock, like 13:30.",
        },
    },
    "required": ["customer_id", "title"],
    "additionalProperties": False,
}


@tool(
    name="create_service_ticket",
    title="Create service ticket",
    access="write",
    confirm=False,
    description="Opens a service ticket for a customer, optionally scheduled for a date and time.",
    details=(
        "Creates a Contractor Foreman service ticket for a customer from the Directory: title, description, an "
        "optional project and the planned service date and time. The service address is the customer's (or the "
        "project's). With a date it is Scheduled, without one Unscheduled. Technicians are assigned in the app. "
        "The customer is not notified. Returns the saved ticket, with service_time on the 12-hour clock (02:00 PM)."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /service-tickets",
    example_response=EXAMPLE_TICKET,
)
async def create_service_ticket(ctx: ToolContext, args: dict[str, Any]) -> Any:
    payload: dict[str, Any] = {
        "customer_id": args["customer_id"],
        "title": args["title"].strip(),
        "address_from": "project" if args.get("project_id") else "directory",
        "access_to_custom_fields": 0,
    }
    if args.get("project_id"):
        payload["project_id"] = args["project_id"]
    ticket_id = created_id(await call(ctx, "service-ticket/add", payload), "ticketId")
    # The add form keeps only the header; the panel saves the rest as field edits (dates as YYYY-MM-DD).
    update: dict[str, Any] = {}
    if args.get("description"):
        update["description"] = args["description"].strip()
    if args.get("service_date"):
        update["service_date"] = args["service_date"]
        update["job_status"] = await status_id(ctx, "service_ticket_job_status", "ticket_status_scheduled")
    if args.get("service_time"):
        update["service_time"] = args["service_time"]
    if update:
        await call(ctx, "service-ticket/update-service-ticket-details", {"service_ticket_id": ticket_id, **update})
    return await read_ticket(ctx, ticket_id)
