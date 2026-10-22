"""Get sub-contract: one sub-contract with its scope items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, date_format, first_record, text
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import item_out, sub_contract_out
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"sub_contract_id": {"type": "integer", "description": "sub_contract_id from list_sub_contracts."}},
    "required": ["sub_contract_id"],
    "additionalProperties": False,
}

EXAMPLE_SC: dict[str, Any] = {
    "sub_contract_id": 455228,
    "agreement_number": "BP-2001-01",
    "subject": "Painting",
    "contractor_id": 6819063,
    "contractor": "Craig Donovan (Donovan's Painting)",
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "date": "2024-01-15",
    "total": 10000.0,
    "billed": 0.0,
    "paid": None,
    "balance": None,
    "retainage_percent": 10.0,
    "status": "Approved",
    "issued_by": "Sam Ortega",
    "scope_of_work": "Painting of interior walls, hallway and bathrooms as per plans dated 02-20-2020",
    "items": [
        {
            "item_id": 894623,
            "description": "Painting subcontractor services",
            "type": "subcontractor",
            "quantity": 1,
            "unit": "ls",
            "unit_cost": 10000.0,
            "total": 10000.0,
            "cost_code": "Painting",
        }
    ],
}


async def read_sub_contract(ctx: ToolContext, sc_id: int) -> dict[str, Any]:
    row = first_record(await call(ctx, f"sub-contracts/{sc_id}"))
    if not row.get("sub_contract_id"):
        raise ToolError("Contractor Foreman did not find that sub-contract.", ErrorCode.TARGET_ERROR)
    out = sub_contract_out(row, await date_format(ctx))
    out["scope_of_work"] = text(row.get("scope_or_work_note"))
    items = await call(ctx, f"sub-contracts/{sc_id}/get-sub-contractor-items")
    out["items"] = [item_out(i) for i in items.get("data") or [] if isinstance(i, dict)]
    return out


@tool(
    name="get_sub_contract",
    title="Get sub-contract",
    access="read",
    confirm=False,
    description="One sub-contract with subcontractor, amounts, retainage, scope of work and items.",
    details=(
        "Reads one Contractor Foreman sub-contract by sub_contract_id: what list_sub_contracts gives plus the "
        "scope of work text (HTML as saved) and the items added in the app, with quantity, unit cost, total and "
        "cost code. paid and balance come back null here. list_sub_contracts has them."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /sub-contracts/{sub_contract_id}",
    example_response=EXAMPLE_SC,
)
async def get_sub_contract(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read_sub_contract(ctx, args["sub_contract_id"])
