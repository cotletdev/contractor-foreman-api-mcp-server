"""Who is signed in: the panel's own app data (POST /api/get-app-data), for "Signed in as ..."."""

from __future__ import annotations

from typing import TYPE_CHECKING

from contractor_foreman_api_mcp.contractor_foreman.client import api
from contractor_foreman_api_mcp.core.errors import AuthExpiredError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext


async def whoami(ctx: ToolContext) -> str | None:
    """None only when Contractor Foreman says signed out; any other failure raises (detection tries again later)."""
    try:
        body = await api(ctx, "get-app-data")
    except AuthExpiredError:
        return None
    me = ((body.get("data") or {}).get("user") or {}).get("data") or {}
    name = me.get("display_name") or " ".join(p for p in (me.get("first_name"), me.get("last_name")) if p).strip()
    email = me.get("email")
    return f"{name} ({email})" if name and email else name or email or None
