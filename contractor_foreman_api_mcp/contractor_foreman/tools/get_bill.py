"""Get bill: one vendor bill with its line items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    call,
    date_format,
    first_record,
    statuses,
    text,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import bill_out, item_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"bill_id": {"type": "integer", "description": "bill_id from list_bills."}},
    "required": ["bill_id"],
    "additionalProperties": False,
}

EXAMPLE_BILL: dict[str, Any] = {
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
    "terms": None,
    "items": [
        {
            "item_id": 5479597,
            "description": "2x2 acoustic ceiling tiles, case of 16",
            "type": "material",
            "quantity": 3,
            "unit": "case",
            "unit_cost": 89.5,
            "total": 268.5,
            "cost_code": None,
        }
    ],
}


async def read_bill(ctx: ToolContext, bill_id: int) -> dict[str, Any]:
    row = first_record(await call(ctx, f"bills/{bill_id}"))
    if not row.get("bill_id"):
        raise ToolError("Contractor Foreman did not find that bill.", ErrorCode.TARGET_ERROR)
    out = bill_out(row, await date_format(ctx))
    status_id = out.pop("status_id", None)
    if not out["status"]:
        out["status"] = {r["id"]: r["name"] for r in await statuses(ctx, "bill_status")}.get(status_id)
    out["terms"] = text(row.get("term_name"))
    out["items"] = [item_out(i) for i in row.get("items") or [] if isinstance(i, dict)]
    return out


@tool(
    name="get_bill",
    title="Get bill",
    access="read",
    confirm=False,
    description="One vendor bill with its line items, dates, total, balance due and status.",
    details=(
        "Reads one Contractor Foreman bill by bill_id: what list_bills gives plus the payment terms and every line "
        "item with description, cost type, quantity, unit, unit cost, total and cost code."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /bills/{bill_id}",
    example_response=EXAMPLE_BILL,
)
async def get_bill(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_bill(ctx, args["bill_id"])
