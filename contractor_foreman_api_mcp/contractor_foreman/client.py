"""Contractor Foreman panel requests, recorded 21.10.2026.

The panel (app.contractorforeman.net, React Router) sends its API calls from a web worker as plain
`fetch` to same-host `/api/...` paths: JSON bodies with `content-type: text/plain;charset=UTF-8`, no auth
header, only the `_session__240322` cookie. A signed-out call still answers HTTP 200, with
`{"statusCode": 401, "unauthorize": true}` in the body, so the core cannot see it: `api` turns it into
`auth_expired`.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.core.errors import AuthExpiredError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

APP = "https://app.contractorforeman.net"
_HEADERS = {"content-type": "text/plain;charset=UTF-8", "origin": APP, "referer": f"{APP}/"}


async def api(ctx: ToolContext, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST one panel API call and return its JSON. Raises `auth_expired` when the app says signed out."""
    response = await ctx.call("POST", f"{APP}/api/{path}", data=json.dumps(payload or {}), headers=_HEADERS)
    body: dict[str, Any] = response.json()
    if body.get("unauthorize") or body.get("statusCode") == 401:
        raise AuthExpiredError("The app signed this account out. Reconnect it in the console.")
    return body
