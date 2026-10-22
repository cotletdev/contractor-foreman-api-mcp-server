"""Add project note: a new note on a project's Notes tab."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call
from contractor_foreman_api_mcp.contractor_foreman.tools._ops_notes import EXAMPLE_NOTE, note_out
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "integer", "description": "The project's numeric id (list_projects)."},
        "title": {"type": "string", "maxLength": 200},
        "text": {"type": "string", "minLength": 1, "maxLength": 10000},
    },
    "required": ["project_id", "text"],
    "additionalProperties": False,
}


@tool(
    name="add_project_note",
    title="Add project note",
    access="write",
    confirm=False,
    description="Adds a note to a project's Notes tab.",
    details=(
        "Writes a note on a Contractor Foreman project's Notes tab as the signed-in user, with an optional "
        "title. It is visible to the company's users with access to the project. Nobody is notified. Returns the "
        "saved note."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /projects/{project_id}/notes",
    example_response=EXAMPLE_NOTE,
)
async def add_project_note(ctx: ToolContext, args: dict[str, Any]) -> Any:
    project = str(args["project_id"])
    body = await call(
        ctx,
        "common/note-add-update",
        {
            "isCommonNotes": 1,
            "recordId": project,
            "moduleKey": "projects",
            "projectId": args["project_id"],
            "title": (args.get("title") or "").strip(),
            "description": args["text"].strip(),
        },
    )
    return note_out(body.get("data") or {})
