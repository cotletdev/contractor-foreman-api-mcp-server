"""Create bill: Bills, Add, then its line items, the way the panel saves a vendor bill."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    app_date,
    call,
    created_id,
    date_format,
)
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_purchasing import ITEMS_SCHEMA, items_in
from contractor_foreman_api_mcp.contractor_foreman.tools.get_bill import EXAMPLE_BILL, read_bill
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "vendor_id": {"type": "integer", "description": "A vendor's contact_id (list_contacts type vendor)."},
        "number": {"type": "string", "minLength": 1, "maxLength": 50, "description": "The vendor's invoice number."},
        "project_id": {"type": "integer", "description": "The project the cost belongs to."},
        "subject": {"type": "string", "maxLength": 200},
        "bill_date": {**DATE_SCHEMA, "description": "YYYY-MM-DD. Default: today."},
        "due_date": DATE_SCHEMA,
        "notes": {"type": "string", "maxLength": 2000},
        "items": ITEMS_SCHEMA,
    },
    "required": ["vendor_id", "number", "items"],
    "additionalProperties": False,
}

BILLS_MODULE_ID = 78


@tool(
    name="create_bill",
    title="Create bill",
    access="write",
    confirm=False,
    description="Records a vendor bill with its line items, optionally against a project.",
    details=(
        "Enters a bill from a vendor in Contractor Foreman: the vendor's invoice number, bill and due date, "
        "subject, notes and line items (description, quantity, unit, unit cost, cost type). With a project_id "
        "the cost shows in that project's job costing. The bill starts Open and nothing is paid or sent. "
        "Returns the saved bill."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /bills",
    example_response=EXAMPLE_BILL,
)
async def create_bill(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fmt = await date_format(ctx)
    payload: dict[str, Any] = {
        "supplier_id": args["vendor_id"],
        "custom_bill_id": args["number"].strip(),
        "access_to_custom_fields": 0,
    }
    if args.get("project_id"):
        payload["project_id"] = args["project_id"]
    payload["order_date"] = (
        app_date(args["bill_date"], fmt) if args.get("bill_date") else datetime.now(UTC).strftime(fmt)
    )
    created = await call(ctx, "bills/add", payload)
    bill_id = created_id(created, "bill_id")
    # The add form saves only the header; subject, due date and notes are inline edits (dates as YYYY-MM-DD).
    update: dict[str, Any] = {k: args[k].strip() for k in ("subject", "notes") if args.get(k)}
    for key, field in (("due_date", "due_date"), ("bill_date", "order_date")):
        if args.get(key):
            update[field] = args[key]
    if update:
        await call(ctx, f"bills/{bill_id}/update", {"module_id": BILLS_MODULE_ID, **update})
    await call(ctx, f"bills/{bill_id}/add-bill-items", {"items": items_in(args["items"])})
    return await read_bill(ctx, bill_id)
