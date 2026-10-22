"""List sub-contracts: Sub-Contracts with subcontractors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import CURSOR_SCHEMA, LIMIT_SCHEMA
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import (
    LIST_PROPS,
    list_records,
    sub_contract_out,
)
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
    "paid": 0.0,
    "balance": 10000.0,
    "retainage_percent": 10.0,
    "status": "Approved",
    "issued_by": "Sam Ortega",
}


@tool(
    name="list_sub_contracts",
    title="List sub-contracts",
    access="read",
    confirm=False,
    description="Sub-contracts with subcontractor, project, amount, billed, paid, balance and status.",
    details=(
        "Reads the Contractor Foreman Sub-Contracts list, newest first: agreement number, subject, "
        "subcontractor, project, date, contract total, amount billed and paid, balance, retainage percent and "
        "status (Draft, Submitted, Committed, Approved ...). Filter by project or search."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /sub-contracts",
    example_response={"sub_contracts": [EXAMPLE_ROW], "next_cursor": None},
)
async def list_sub_contracts(ctx: ToolContext, args: dict[str, Any]) -> Any:
    found, cursor = await list_records(ctx, args, "sub-contracts", "subContracts", sub_contract_out)
    return {"sub_contracts": found, "next_cursor": cursor}
