"""List cost codes: the company's cost codes (CSI style) for line items and job costing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import call
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"search": {"type": "string", "description": "Matches the code or the name."}},
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "cost_codes": [{"cost_code_id": "72", "code": "06100", "name": "Framing, Ceilings", "parent_id": "6"}]
}


@tool(
    name="list_cost_codes",
    title="List cost codes",
    access="read",
    description="The company's cost codes, to put on estimate, change order and invoice items.",
    details=(
        "Every active cost code with its code number, name and parent group. cost_code_id is what the item "
        "tools take. search narrows by code or name."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /cost-codes",
    example_response=EXAMPLE_RESPONSE,
    credits=20,
)
async def list_cost_codes(ctx: ToolContext, args: dict[str, Any]) -> Any:
    rows = (await call(ctx, "cost-codes", {})).get("data") or []
    wanted = (args.get("search") or "").strip().lower()
    codes = [
        {
            "cost_code_id": str(row.get("code_id")),
            "code": row.get("csi_code") or None,
            "name": row.get("cost_code_name") or row.get("csi_name"),
            "parent_id": str(row["parent_id"]) if row.get("parent_id") else None,
        }
        for row in rows
        if not row.get("is_deleted")
    ]
    if wanted:
        codes = [code for code in codes if wanted in f"{code['code'] or ''} {code['name'] or ''}".lower()]
    return {"cost_codes": codes}
