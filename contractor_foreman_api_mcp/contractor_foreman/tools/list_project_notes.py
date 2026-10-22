"""List project notes: a project's Notes tab."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_notes import EXAMPLE_NOTE, note_out
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"project_id": {"type": "integer", "description": "The project's numeric id (list_projects)."}},
    "required": ["project_id"],
    "additionalProperties": False,
}


@tool(
    name="list_project_notes",
    title="List project notes",
    access="read",
    confirm=False,
    description="The notes on a project's Notes tab, with author and time.",
    details=(
        "Reads the notes kept on a Contractor Foreman project's Notes tab, oldest first: title, text, who added "
        "it, when (in the account's date format) and how many files are attached."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/{project_id}/notes",
    example_response={"notes": [EXAMPLE_NOTE]},
)
async def list_project_notes(ctx: ToolContext, args: dict[str, Any]) -> Any:
    body = await call(ctx, "common/get-common-notes", {"record_id": args["project_id"], "module_key": "projects"})
    return {"notes": [note_out(r) for r in body.get("data") or [] if isinstance(r, dict)]}
