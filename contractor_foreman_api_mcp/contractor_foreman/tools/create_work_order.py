"""Create work order: Work Orders, Add."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    DATE_SCHEMA,
    app_date,
    call,
    created_id,
    date_format,
)
from contractor_foreman_api_mcp.contractor_foreman.tools.get_work_order import EXAMPLE_WO, read_work_order
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "integer", "description": "The project the work is on."},
        "subject": {"type": "string", "minLength": 1, "maxLength": 200},
        "description": {"type": "string", "maxLength": 5000, "description": "What has to be done."},
        "start_date": {**DATE_SCHEMA, "description": "YYYY-MM-DD. Default: today."},
        "end_date": {**DATE_SCHEMA, "description": "YYYY-MM-DD, not before start_date. Default: today."},
    },
    "required": ["project_id", "subject"],
    "additionalProperties": False,
}


@tool(
    name="create_work_order",
    title="Create work order",
    access="write",
    confirm=False,
    description="Creates an Open work order on a project with subject, description and dates.",
    details=(
        "Creates a Contractor Foreman work order in Open status on a project, issued by the signed-in user, for "
        "the project's customer: subject, description, start and end date. It has no line items. Nobody is "
        "notified, and sending it to the customer stays a step in the app. update_work_order_status moves it on. "
        "Returns the saved order."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /work-orders",
    example_response=EXAMPLE_WO,
)
async def create_work_order(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fmt = await date_format(ctx)
    payload: dict[str, Any] = {
        "project_id": args["project_id"],
        "subject": args["subject"].strip(),
        "access_to_custom_fields": 0,
    }
    if args.get("start_date"):
        payload["order_date"] = app_date(args["start_date"], fmt)
    if args.get("end_date"):
        payload["end_date"] = app_date(args["end_date"], fmt)
    work_order_id = created_id(await call(ctx, "workorder/add-workorder", payload), "work_order_id")
    if args.get("description"):
        await call(ctx, f"workorder/{work_order_id}/update", {"description": args["description"].strip()})
    return await read_work_order(ctx, work_order_id)
