"""Create invoice: a draft invoice for a project or customer with priced line items."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    LINE_ITEM,
    call,
    number,
    plain,
    project_customer,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._invoices import add_items, detail, row_out, update
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "description": "From list_projects. Its customer is billed."},
        "customer_id": {"type": "string", "description": "Directory customer id. Needed without a project."},
        "invoice_date": {"type": "string", "format": "date", "description": "Default: today."},
        "due_date": {"type": "string", "format": "date"},
        "items": {"type": "array", "maxItems": 100, "items": LINE_ITEM},
        "description": {"type": "string", "description": "Shown on the invoice. Needs due_date in the same call."},
        "number": {"type": "string", "maxLength": 30, "description": "Your own number. Default: the app's next."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "invoice_id": "2049756",
    "number": "10",
    "status": "draft",
    "status_name": "Draft",
    "project_id": "1678167",
    "project_name": "Kitchen Upgrade",
    "customer_id": "6819060",
    "customer_name": "Dana Whitfield (Whitfield Homes)",
    "invoice_date": "2026-10-21",
    "due_date": "2026-11-20",
    "total": 1500.0,
    "balance_due": 1500.0,
    "overdue": False,
    "description": "Progress billing 1 of 3",
    "items": [
        {
            "item_id": "10930638",
            "name": "Pantry cabinet installation, progress billing",
            "type": "other",
            "quantity": 1,
            "unit": "ls",
            "unit_cost": 1500.0,
            "markup_percent": None,
            "total": 1500.0,
            "cost_code": None,
            "description": None,
            "section": None,
        }
    ],
}


@tool(
    name="create_invoice",
    title="Create invoice",
    access="write",
    description="Creates a draft invoice for a project or customer, with priced line items.",
    details=(
        "Saves a new invoice in the Draft status. With project_id it bills that project's customer. Without "
        "one, customer_id is required. A description needs due_date in the same call. items are plain "
        "priced lines (name, type, quantity, unit, unit cost in dollars, markup percent). It is not sent. "
        "update_invoice with status submitted marks it sent and lets record_payment take payments. "
        "send_invoice emails it after your OK."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /invoices",
    example_response=EXAMPLE_RESPONSE,
)
async def create_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    if args.get("description") and not args.get("due_date"):
        raise ToolError("A description needs due_date too.", ErrorCode.INVALID_INPUT)
    project = number(args.get("project_id"))
    customer = number(args.get("customer_id"))
    if not customer:
        if not project:
            raise ToolError("Pass project_id or customer_id.", ErrorCode.INVALID_INPUT)
        customer = await project_customer(ctx, project)
    payload: dict[str, Any] = {
        "custom_invoice_id": args.get("number", ""),
        "customer_id": customer,
        "invoice_date": args.get("invoice_date") or datetime.datetime.now(tz=datetime.UTC).date().isoformat(),
        "access_to_custom_fields": 0,
    }
    if project:
        payload["project_id"] = project
    invoice_id = str(((await call(ctx, "invoices/add", payload)).get("data") or {}).get("invoice_id") or "")
    if not number(invoice_id):
        raise ToolError("Contractor Foreman did not return the new invoice.", ErrorCode.TARGET_ERROR)
    fields = {key: args[key] for key in ("due_date", "description") if args.get(key)}
    if fields:
        await update(ctx, invoice_id, fields)
    items = await add_items(ctx, invoice_id, args["items"]) if args.get("items") else []
    data = await detail(ctx, invoice_id)
    return {**row_out(data), "description": plain(data.get("description")), "items": items}
