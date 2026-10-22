"""Update project: the inline fields of the project's Details tab (`projects/{id}/update`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import panel
from contractor_foreman_api_mcp.contractor_foreman.tools.create_project import TYPES, project_fields
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import (
    EXAMPLE_RESPONSE as PROJECT,
)
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import (
    PROJECT_ID,
    project_detail,
    read_project,
)
from contractor_foreman_api_mcp.contractor_foreman.tools.list_projects import STATUSES
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": PROJECT_ID,
        "name": {"type": "string", "minLength": 1},
        "status": {"type": "string", "enum": STATUSES, "description": "New stage, e.g. started or completed."},
        "type": {"type": "string", "enum": TYPES},
        "street": {"type": "string"},
        "street2": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "zip": {"type": "string"},
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "description": {"type": "string"},
    },
    "required": ["project_id"],
    "additionalProperties": False,
}


@tool(
    name="update_project",
    title="Update project",
    access="write",
    description="Change a project's name, stage, type, address, dates or description.",
    details=(
        "Changes only the fields you pass and returns the project as get_project shows it. A completed "
        "project drops out of list_projects unless include_completed is true. Editing the schedule can move "
        "the project dates again. Nothing reaches the customer, so this tool runs without asking."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /projects/{project_id}",
    example_response=PROJECT,
)
async def update_project(ctx: ToolContext, args: dict[str, Any]) -> Any:
    project_id = args["project_id"]
    fields = project_fields(args)
    if not fields:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    await read_project(ctx, project_id)
    await panel(ctx, f"projects/{project_id}/update", {"module_key": "projects", **fields})
    return project_detail(await read_project(ctx, project_id))
