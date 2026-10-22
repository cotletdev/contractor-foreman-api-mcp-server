"""Create punchlist: the panel's "Add Punchlist" form (`punchlists/add`: project and name)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import panel
from contractor_foreman_api_mcp.contractor_foreman.tools._punchlists import EXAMPLE_PUNCHLIST, read_punchlist
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import PROJECT_ID
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": PROJECT_ID,
        "name": {"type": "string", "minLength": 1, "description": "Punchlist name, e.g. Final walkthrough - kitchen."},
    },
    "required": ["project_id", "name"],
    "additionalProperties": False,
}


@tool(
    name="create_punchlist",
    title="Create punchlist",
    access="write",
    description="New, empty punchlist on a project.",
    details=(
        "Adds an empty punchlist to the project and returns it as get_punchlist shows it. Items cannot be "
        "added through this tool yet, so add them in Contractor Foreman. Nobody is assigned or notified, so "
        "this tool runs without asking."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /punchlists",
    example_response=EXAMPLE_PUNCHLIST,
)
async def create_punchlist(ctx: ToolContext, args: dict[str, Any]) -> Any:
    name = args["name"].strip()
    if not name:
        raise ToolError("name must not be empty.", ErrorCode.INVALID_INPUT)
    body = await panel(
        ctx, "punchlists/add", {"project_id": args["project_id"], "punchlist_name": name, "access_to_custom_fields": 0}
    )
    punchlist_id = str((body.get("data") or {}).get("punchlist_id") or "")
    if not punchlist_id:
        raise ToolError("Contractor Foreman did not return the new punchlist.", ErrorCode.TARGET_ERROR)
    return await read_punchlist(ctx, punchlist_id)
