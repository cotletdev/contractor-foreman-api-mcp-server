"""Update estimate: status, title, dates and text fields of one estimate (estimate/{id}/update)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import (
    ESTIMATE_STATUSES,
    call,
    dollars,
    iso,
    key_of,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "estimate_id": {"type": "string", "minLength": 1, "description": "From list_estimates."},
        "status": {"type": "string", "enum": list(ESTIMATE_STATUSES)},
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "description": {"type": "string"},
        "inclusions": {"type": "string"},
        "exclusions": {"type": "string"},
        "estimate_date": {"type": "string", "format": "date"},
        "expire_date": {"type": "string", "format": "date"},
    },
    "required": ["estimate_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "estimate_id": "1616575",
    "title": "Pantry Cabinet Addition",
    "status": "approved",
    "status_name": "Approved",
    "estimate_date": "2026-10-21",
    "expire_date": "2026-11-20",
    "total": 1338.0,
}

_FIELDS = {
    "title": "title",
    "description": "description",
    "inclusions": "inclusion",
    "exclusions": "exclusion",
    "estimate_date": "estimate_date",
    "expire_date": "expire_date",
}


@tool(
    name="update_estimate",
    title="Update estimate",
    access="write",
    description="Changes an estimate's status, title, dates, description, inclusions or exclusions.",
    details=(
        "Sets only the fields you pass. status moves the estimate on the Estimates board: estimating, "
        "pending_approval, on_hold, re_estimating, approved, completed or lost. Marking it approved here does "
        "not email anyone. send_estimate sends it. Line items change with add_estimate_items and "
        "remove_estimate_items."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /estimates/{estimate_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def update_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    estimate_id = str(args["estimate_id"])
    payload = {key: args[name] for name, key in _FIELDS.items() if name in args}
    if args.get("status"):
        payload["approval_type"] = ESTIMATE_STATUSES[args["status"]]
    if not payload:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    await call(ctx, f"estimate/{estimate_id}/update", payload)
    data = (await call(ctx, f"estimate/{estimate_id}/detail", {})).get("data") or {}
    return {
        "estimate_id": estimate_id,
        "title": data.get("title"),
        "status": key_of(ESTIMATE_STATUSES, data.get("approval_type_key")),
        "status_name": data.get("approval_type_name"),
        "estimate_date": iso(data.get("estimate_date")),
        "expire_date": iso(data.get("expire_date")),
        "total": dollars(data.get("total")),
    }
