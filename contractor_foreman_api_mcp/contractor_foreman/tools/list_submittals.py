"""List submittals: Submittals sent for approval (shop drawings, product data)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import submittal_out
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
    "submittal_id": 134560,
    "number": "3",
    "title": "Vent Hoods and Filtration",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "status": "Draft",
    "date_received": "2024-01-01",
    "due_date": "2024-01-15",
    "assigned_to": None,
    "approved_by": None,
}


@tool(
    name="list_submittals",
    title="List submittals",
    access="read",
    confirm=False,
    description="Submittals with project, status, date received, due date and approver.",
    details=(
        "Reads the Contractor Foreman Submittals list, newest first: number, title, project, status (Draft, "
        "Submitted, Pending, Response Received, Approved, Rejected), date received, due date, who it is "
        "assigned to and who approved it. Filter by project or search."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /submittals",
    example_response={"submittals": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_submittals(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "submittal", "submittal", submittal_out)
    return {"submittals": found, "next_cursor": cursor}
