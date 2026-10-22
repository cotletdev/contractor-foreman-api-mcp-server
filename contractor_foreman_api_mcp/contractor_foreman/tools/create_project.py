"""Create project: the "Add Project" form (`projects/addProject`), then dates via `projects/{id}/update`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import compact, panel, parse_date
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import EXAMPLE_RESPONSE as PROJECT
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import project_detail, read_project
from contractor_foreman_api_mcp.contractor_foreman.tools.list_projects import STATUSES
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# Global project types (`global/types`, type "project_type", 21.10.2026).
TYPES = [
    "residential",
    "commercial",
    "factory",
    "infrastructure",
    "multi_use_project",
    "public_works",
    "time_and_material",
]

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Project name, e.g. Kitchen remodel - Oak St."},
        "number": {
            "type": "string",
            "description": "Project number. Default: the next number when the account numbers projects itself.",
        },
        "customer_id": {
            "type": "string",
            "pattern": "^[0-9]+$",
            "description": "The customer's contact_id from list_contacts.",
        },
        "type": {"type": "string", "enum": TYPES, "default": "residential"},
        "status": {"type": "string", "enum": STATUSES, "default": "pending"},
        "street": {"type": "string"},
        "street2": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "zip": {"type": "string"},
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "description": {"type": "string"},
    },
    "required": ["name", "customer_id"],
    "additionalProperties": False,
}


async def next_number(ctx: ToolContext) -> str:
    body = await panel(ctx, "common/get-module-auto-number", {"module_id": 1, "module_key": "projects"})
    data = body.get("data") or {}
    last = int(data.get("last_primary_id") or 0)
    if last <= 0:
        raise ToolError(
            "This account numbers projects by hand: give a project number, e.g. 2026-014.", ErrorCode.INVALID_INPUT
        )
    return str(last + int(data.get("need_to_increment") or 0))


def project_fields(args: dict[str, Any]) -> dict[str, Any]:
    """Input fields that `projects/{id}/update` takes, under the panel's names."""
    fields: dict[str, Any] = {
        "project_name": args.get("name"),
        "project_status": args.get("status"),
        "project_type": args.get("type"),
        "description": args.get("description"),
        "address1": args.get("street"),
        "address2": args.get("street2"),
        "city": args.get("city"),
        "state": args.get("state"),
        "zip": args.get("zip"),
    }
    for key in ("start_date", "end_date"):
        if args.get(key):
            fields[key] = parse_date(args[key], key).isoformat()
    if fields.get("start_date") and fields.get("end_date") and fields["end_date"] < fields["start_date"]:
        raise ToolError("end_date must not be before start_date.", ErrorCode.INVALID_INPUT)
    return compact(fields)


@tool(
    name="create_project",
    title="Create project",
    access="write",
    description="New project for a customer, with number, type, stage, address and dates.",
    details=(
        "Adds a project in the stage you give (default pending) for a customer from your Directory. Without "
        "number the account's next project number is used. Accounts that number projects by hand need one. "
        "The project reaches nobody outside your company, so this tool runs without asking. Returns the "
        "project as get_project shows it."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /projects",
    example_response=PROJECT,
)
async def create_project(ctx: ToolContext, args: dict[str, Any]) -> Any:
    fields = project_fields(args)
    dates = {key: fields.pop(key) for key in ("start_date", "end_date") if key in fields}
    fields.pop("description", None)
    number = (args.get("number") or "").strip() or await next_number(ctx)
    body = await panel(
        ctx,
        "projects/addProject",
        {
            **fields,
            "customer_id": args["customer_id"],
            "project_id": number,
            "project_type": args.get("type") or "residential",
            "project_status": args.get("status") or "pending",
            "default_tax_rate_id": 0,
            "access_to_custom_fields": 0,
            "latitude": 0,
            "longitude": 0,
            "copy_templates_module": [],
        },
    )
    new_id = str((body.get("data") or {}).get("inserted_id") or "")
    if not new_id:
        raise ToolError("Contractor Foreman did not return the new project.", ErrorCode.TARGET_ERROR)
    later = {**dates, **({"description": args["description"]} if args.get("description") else {})}
    if later:
        await panel(ctx, f"projects/{new_id}/update", {"module_key": "projects", **later})
    return project_detail(await read_project(ctx, new_id))
