"""Punchlist shapes shared by the punchlist tools.

The new app's `/api/punchlists/*` answers lists, details, new punchlists and renames from the session cookie.
Its item calls (`{id}/get-item-list`, `{id}/add-item`) answer 500 on every body tried (21.10.2026), also on a
punchlist made by this account: the Punchlists page still redirects to the old PHP panel, which reaches items
through `api.contractorforeman.net/service.php` with a bearer token only that page carries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import iso, number, panel, text
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

PUNCHLIST_ID = {"type": "string", "pattern": "^[0-9]+$", "description": "punchlist_id from list_punchlists."}

EXAMPLE_PUNCHLIST: dict[str, Any] = {
    "punchlist_id": "72520",
    "number": 2,
    "name": "Final walkthrough - kitchen",
    "project_id": "1678216",
    "project_number": "HR-1001",
    "project_name": "Kitchen remodel - Oak St",
    "project_address": "412 Oak St, Raleigh, NC 27601",
    "customer": "John Pence",
    "open_items": 0,
    "completed_items": 0,
    "created_by": "Michael Howard",
    "created_date": "2026-10-21",
}


def punchlist_view(data: dict[str, Any]) -> dict[str, Any]:
    street = ", ".join(
        part
        for part in [
            text(data.get("prj_address1")),
            text(data.get("prj_city")),
            " ".join(p for p in [text(data.get("prj_state")), text(data.get("prj_zip"))] if p) or None,
        ]
        if part
    )
    return {
        "punchlist_id": str(data.get("punchlist_id")),
        "number": data.get("company_punchlist_id"),
        "name": text(data.get("punchlist_name")),
        "project_id": str(data.get("project_id")),
        "project_number": text(data.get("prj_id")),
        "project_name": text(data.get("project_name")),
        "project_address": street or None,
        "customer": text(data.get("customer_name")),
        "open_items": int(number(data.get("incomplete_items"))),
        "completed_items": int(number(data.get("completed_items"))),
        "created_by": text(data.get("employee")),
        "created_date": iso(data.get("date_added")),
    }


async def read_punchlist(ctx: ToolContext, punchlist_id: str) -> dict[str, Any]:
    body = await panel(ctx, f"punchlists/{punchlist_id}/get-punchlist-detail", {})
    data = body.get("data")
    if not isinstance(data, dict) or not data.get("punchlist_id"):
        raise ToolError(f"No punchlist {punchlist_id} in this account. Use list_punchlists.", ErrorCode.TARGET_ERROR)
    return punchlist_view(data)
