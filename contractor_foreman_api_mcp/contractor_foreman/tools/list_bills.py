"""List bills: Bills, the vendor bills to pay."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA, statuses
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import LIST_PROPS, bill_out, list_records
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
    "bill_id": 2922734,
    "number": "TLS-4471",
    "subject": "Ceiling tiles and grid",
    "vendor_id": 6819139,
    "vendor": "Dana Whitfield (Triangle Lumber Supply)",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "bill_date": "2026-10-21",
    "due_date": "2026-11-20",
    "total": 268.5,
    "balance_due": 268.5,
    "status": "Open",
    "notes": "Invoice TLS-4471, net 30",
}


@tool(
    name="list_bills",
    title="List bills",
    access="read",
    confirm=False,
    description="Vendor bills with vendor, project, dates, total, balance due and status.",
    details=(
        "Reads the Contractor Foreman Bills list, newest first: bill number, subject, vendor, project, bill "
        "date, due date, total, balance still due and status (Open, Paid). Filter by project or search. "
        "get_bill adds the line items."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /bills",
    example_response={"bills": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_bills(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "bills", "data", bill_out)
    names = {row["id"]: row["name"] for row in await statuses(ctx, "bill_status")}
    for bill in found:
        bill["status"] = bill["status"] or names.get(bill.pop("status_id"))
        bill.pop("status_id", None)
    return {"bills": found, "next_cursor": cursor}
