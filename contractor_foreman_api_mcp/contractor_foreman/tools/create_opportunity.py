"""Create opportunity: Opportunities, Add."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    app_date,
    call,
    created_id,
    date_format,
    first_record,
    to_cents,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_opportunities import (
    EXAMPLE_OPPORTUNITY,
    STAGES,
    opportunity_out,
)
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "customer_id": {"type": "integer", "description": "A customer's contact_id (list_contacts type customer)."},
        "name": {"type": "string", "minLength": 1, "maxLength": 200},
        "number": {
            "type": "string",
            "maxLength": 50,
            "description": "Your opportunity number. Left out: OPP- and the UTC date and time, as OPP-261021-1213.",
        },
        "project_type": {"type": "string", "enum": ["commercial", "residential"], "default": "commercial"},
        "stage": {"type": "string", "enum": STAGES, "default": "received"},
        "score": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
        "budget": {"type": "number", "minimum": 0, "description": "Expected value in the account currency."},
        "est_sales_date": {**DATE_SCHEMA, "description": "Expected sale date, YYYY-MM-DD."},
        "address1": {"type": "string", "maxLength": 200},
        "city": {"type": "string", "maxLength": 100},
        "state": {"type": "string", "maxLength": 50},
        "zip": {"type": "string", "maxLength": 20},
    },
    "required": ["customer_id", "name"],
    "additionalProperties": False,
}


@tool(
    name="create_opportunity",
    title="Create opportunity",
    access="write",
    confirm=False,
    description="Adds a sales opportunity for a customer with stage, score, budget and expected sale date.",
    details=(
        "Creates an opportunity in Contractor Foreman as the Opportunities Add drawer does, for a customer from "
        "the Directory. It is assigned to the signed-in user. Nobody is emailed. The opportunity number must be "
        "unique. Without one it gets OPP- and the UTC date and time (OPP-261021-1213). Returns the saved opportunity."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /opportunities",
    example_response=EXAMPLE_OPPORTUNITY,
)
async def create_opportunity(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fmt = await date_format(ctx)
    number = (args.get("number") or "").strip() or f"OPP-{datetime.now(UTC):%y%m%d-%H%M}"
    payload: dict[str, Any] = {
        "customer_id": args["customer_id"],
        "project_id": number,
        "project_name": args["name"].strip(),
        "project_type": args.get("project_type") or "commercial",
        "stage": f"opportunity_stage_{args.get('stage') or 'received'}",
        "score": str(args.get("score") or 3),
        "type": "opportunity",
        "access_to_custom_fields": 0,
    }
    if args.get("budget") is not None:
        payload["budget_amount"] = to_cents(args["budget"])
    if args.get("est_sales_date"):
        payload["est_sales_date"] = app_date(args["est_sales_date"], fmt)
    for key in ("address1", "city", "state", "zip"):
        if args.get(key):
            payload[key] = args[key].strip()
    created = await call(ctx, "opportunities/add", payload)
    new_id = created_id(created, "inserted_id")
    body = await call(ctx, "opportunities/get-opportunity-detail", {"project_id": new_id, "record_type": "opportunity"})
    return opportunity_out(first_record(body), fmt)
