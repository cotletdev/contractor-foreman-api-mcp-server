"""Get service ticket: one service ticket's detail page."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import ticket_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "service_ticket_id": {"type": "integer", "description": "service_ticket_id from list_service_tickets."}
    },
    "required": ["service_ticket_id"],
    "additionalProperties": False,
}

EXAMPLE_TICKET: dict[str, Any] = {
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
    "priority": "Normal",
    "duration_minutes": 60,
    "address": {"street": "128 Weller Drive", "city": "Thurmont", "state": "MD", "zip": "21788"},
    "customer_phone": "(410) 555-1212",
    "hours_logged": "00:00",
}


async def read_ticket(ctx: ToolContext, ticket_id: int) -> dict[str, Any]:
    body = await call(ctx, "service-ticket/get-service-ticket-details", {"service_ticket_id": ticket_id})
    row = first_record(body)
    if not row.get("service_ticket_id"):
        raise ToolError("Contractor Foreman did not find that service ticket.", ErrorCode.TARGET_ERROR)
    out = ticket_out(row, await date_format(ctx))
    techs = [text(t.get("assignee_name")) for t in row.get("assigned_to") or [] if isinstance(t, dict)]
    out["technicians"] = out["technicians"] or (", ".join(t for t in techs if t) or None)
    out.update(
        {
            "priority": text(row.get("priority_name")),
            "duration_minutes": row.get("service_duration"),
            "address": {
                "street": text(row.get("cust_street")),
                "city": text(row.get("customer_city")),
                "state": text(row.get("customer_state")),
                "zip": text(row.get("cust_zip") or row.get("customer_zip")),
            },
            "customer_phone": text(row.get("customer_cell") or row.get("customer_phone")),
            "hours_logged": text(row.get("timecard_hours")),
        }
    )
    return out


@tool(
    name="get_service_ticket",
    title="Get service ticket",
    access="read",
    confirm=False,
    description="One service ticket with customer, service address, schedule, technicians and priority.",
    details=(
        "Reads one Contractor Foreman service ticket by service_ticket_id: what list_service_tickets gives plus "
        "the priority, planned duration, service address, the customer's phone and the hours logged on it."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /service-tickets/{service_ticket_id}",
    example_response=EXAMPLE_TICKET,
)
async def get_service_ticket(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_ticket(ctx, args["service_ticket_id"])
