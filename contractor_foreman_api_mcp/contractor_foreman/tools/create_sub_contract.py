"""Create sub-contract: Sub-Contracts, Add."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    app_date,
    call,
    created_id,
    date_format,
)
from contractor_foreman_api_mcp.contractor_foreman.tools.get_sub_contract import EXAMPLE_SC, read_sub_contract
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "integer", "description": "The project the work is for."},
        "contractor_id": {"type": "integer", "description": "The subcontractor's contact_id (type contractor)."},
        "subject": {"type": "string", "minLength": 1, "maxLength": 200},
        "agreement_number": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50,
            "description": "Your agreement number, e.g. the project number and a sequence (BP-2001-07).",
        },
        "date": {**DATE_SCHEMA, "description": "YYYY-MM-DD. Default: today."},
    },
    "required": ["project_id", "contractor_id", "subject", "agreement_number"],
    "additionalProperties": False,
}


@tool(
    name="create_sub_contract",
    title="Create sub-contract",
    access="write",
    confirm=False,
    description="Creates a draft sub-contract with a subcontractor on a project.",
    details=(
        "Creates a Contractor Foreman sub-contract in Draft status, issued by the signed-in user, for a project and a"
        " subcontractor from the Directory, with subject, agreement number and date. This API cannot add scope items,"
        " terms or send it for signature. Those stay steps in the app. The subcontractor is not notified. Returns the"
        " saved sub-contract."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /sub-contracts",
    example_response={
        **EXAMPLE_SC,
        "date": "2026-10-21",
        "total": 0.0,
        "retainage_percent": None,
        "status": "Draft",
        "scope_of_work": None,
        "items": [],
    },
)
async def create_sub_contract(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fmt = await date_format(ctx)
    payload: dict[str, Any] = {
        "project_id": args["project_id"],
        "contractor_id": args["contractor_id"],
        "subject": args["subject"].strip(),
        "agreement": args["agreement_number"].strip(),
        "access_to_custom_fields": 0,
    }
    if args.get("date"):
        payload["order_date"] = app_date(args["date"], fmt)
    created = await call(ctx, "sub-contracts/add", payload)
    return await read_sub_contract(ctx, created_id(created, "sub_contract_id"))
