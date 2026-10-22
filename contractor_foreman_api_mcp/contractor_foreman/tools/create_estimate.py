"""Create estimate: a draft estimate for a project or a customer, with its line items in one call."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    LINE_ITEM,
    call,
    dollars,
    number,
    project_customer,
)
from contractor_foreman_api_mcp.contractor_foreman.tools.add_estimate_items import add_items
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "project_id": {"type": "string", "description": "From list_projects. Its customer is used."},
        "customer_id": {"type": "string", "description": "Directory customer id. Needed without a project."},
        "items": {"type": "array", "maxItems": 100, "items": LINE_ITEM},
        "description": {"type": "string", "description": "Scope shown on the estimate."},
        "inclusions": {"type": "string"},
        "exclusions": {"type": "string"},
        "expire_date": {"type": "string", "format": "date"},
    },
    "required": ["title"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "estimate_id": "1616575",
    "number": "5",
    "title": "Pantry Cabinet Addition",
    "status": "estimating",
    "project_id": "1678167",
    "customer_id": "6819060",
    "items": [
        {
            "item_id": "30109600",
            "name": "Cabinet removal labor",
            "type": "labor",
            "quantity": 6,
            "unit": "Hrs",
            "unit_cost": 55.0,
            "markup_percent": None,
            "total": 330.0,
            "cost_code": None,
            "description": None,
            "section": None,
        }
    ],
    "total": 1338.0,
}


@tool(
    name="create_estimate",
    title="Create estimate",
    access="write",
    description="Creates a draft estimate on a project or for a customer, with priced line items.",
    details=(
        "Saves a new estimate in the Estimating status, unit-price billing, dated today. With project_id it "
        "belongs to that project and its customer. Without one, customer_id is required. items are priced "
        "lines (name, type, quantity, unit, unit cost in dollars, markup percent, cost code). The app computes "
        "totals. Nothing is sent: send_estimate does that after your OK. More lines later with "
        "add_estimate_items, other fields with update_estimate."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /estimates",
    example_response=EXAMPLE_RESPONSE,
)
async def create_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    project = number(args.get("project_id"))
    customer = number(args.get("customer_id"))
    if not customer:
        if not project:
            raise ToolError("Pass project_id or customer_id.", ErrorCode.INVALID_INPUT)
        customer = await project_customer(ctx, project)
    payload: dict[str, Any] = {
        "title": args["title"],
        "billing_option": "unit",
        "customer_id": customer,
        "access_to_custom_fields": 0,
    }
    if project:
        payload["project_id"] = project
    estimate_id = str((await call(ctx, "estimate/add", payload)).get("data"))
    if not number(estimate_id):
        raise ToolError("Contractor Foreman did not return the new estimate.", ErrorCode.TARGET_ERROR)
    fields = {
        key: args[name]
        for name, key in (
            ("description", "description"),
            ("inclusions", "inclusion"),
            ("exclusions", "exclusion"),
            ("expire_date", "expire_date"),
        )
        if args.get(name)
    }
    if fields:
        await call(ctx, f"estimate/{estimate_id}/update", fields)
    items = await add_items(ctx, estimate_id, args["items"], None) if args.get("items") else []
    detail = (await call(ctx, f"estimate/{estimate_id}/detail", {})).get("data") or {}
    return {
        "estimate_id": estimate_id,
        "number": detail.get("company_estimate_id"),
        "title": detail.get("title"),
        "status": "estimating",
        "project_id": str(project) if project else None,
        "customer_id": str(customer),
        "items": items,
        "total": dollars(detail.get("total")),
    }
