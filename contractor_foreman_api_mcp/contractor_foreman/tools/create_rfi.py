"""Create RFI: RFI & Notices, Add, type RFI."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import DATE_SCHEMA, call, created_id, date_format
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_field import RFI_TYPE
from contractor_foreman_api_mcp.contractor_foreman.tools.get_rfi import read_rfi
from contractor_foreman_api_mcp.contractor_foreman.tools.list_rfis import EXAMPLE_RFI
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "integer", "description": "The project the question is about."},
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "question": {"type": "string", "minLength": 1, "maxLength": 5000, "description": "The information requested."},
        "reference_area": {"type": "string", "maxLength": 200, "description": "Area or element it refers to."},
        "plan_sheet": {"type": "string", "maxLength": 50, "description": "Plan sheet number."},
        "response_needed_by": DATE_SCHEMA,
    },
    "required": ["project_id", "title", "question"],
    "additionalProperties": False,
}


@tool(
    name="create_rfi",
    title="Create RFI",
    access="write",
    confirm=False,
    description="Drafts a request for information on a project, with the question and a reply-by date.",
    details=(
        "Creates a Contractor Foreman RFI in Draft status on a project, from the signed-in user, dated now: "
        "title, question, the area and plan sheet it refers to and the date a response is needed by. It is not "
        "sent to anyone. Submitting it to the architect or owner stays a step in the app. Returns the saved RFI."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /rfis",
    example_response=EXAMPLE_RFI,
)
async def create_rfi(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fmt = await date_format(ctx)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "type": RFI_TYPE,
        "project_id": args["project_id"],
        "title": args["title"].strip(),
        "info_request": args["question"].strip(),
        "correspondence_date": now.strftime(fmt),
        "correspondence_time": now.strftime("%I:%M %p"),
        "access_to_custom_fields": 0,
    }
    rfi_id = created_id(await call(ctx, "rfi/add", payload), "correspondence_id")
    # The add form keeps title and question only; the rest are field edits on the record, dates as YYYY-MM-DD.
    update: dict[str, Any] = {}
    if args.get("reference_area"):
        update["reference_area_of_question"] = args["reference_area"].strip()
    if args.get("plan_sheet"):
        update["plan_sheet_no"] = args["plan_sheet"].strip()
    if args.get("response_needed_by"):
        update["response_needed_by"] = args["response_needed_by"]
    if update:
        await call(ctx, f"rfi/{rfi_id}/update", update)
    return await read_rfi(ctx, rfi_id)
