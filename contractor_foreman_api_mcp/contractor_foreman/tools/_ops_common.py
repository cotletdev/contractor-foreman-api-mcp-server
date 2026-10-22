"""Shared helpers for the operations tools: directory, leads, time cards, purchasing, field records, notes.

Every call goes through `client.api` (signed-out answers become `auth_expired`). `call` adds the fields the
panel sends with every body and turns the app's own error answers into a `ToolError`. Money is stored in
cents, dates come back in the account's date format (Settings, `date_format`, `%m/%d/%Y` by default).
"""

from __future__ import annotations

import html
import json
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from contractor_foreman_api_mcp.contractor_foreman.client import api
from contractor_foreman_api_mcp.core.errors import AuthExpiredError, ErrorCode, ToolError
from contractor_foreman_api_mcp.core.helpers import limit as clamp_limit

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# Sent by the panel's web worker with every body (MAP "How every call looks"). The time zone is the browser's,
# as the panel's Intl call reports it; clock times in the answers follow it.
_BASE = {"version": "web", "from": "panel", "force_login": 0}


def _zone(ctx: ToolContext) -> dict[str, str]:
    try:
        zone = ZoneInfo(ctx.profile.timezone or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    return {"timezone": datetime.now(zone).strftime("%z"), "tzid": str(zone.key)}


# Directory record types (`type` in the directory answers), recorded 21.10.2026.
CONTACT_TYPES: dict[str, int] = {"employee": 2, "customer": 3, "contractor": 4, "vendor": 22, "misc_contact": 23}
LEAD_TYPE = 204
# The panel module behind each directory type; add-directory needs it.
CONTACT_MODULES: dict[int, int] = {2: 23, 3: 22, 4: 24, 22: 25, 23: 38, 204: 71}
TYPE_NAMES: dict[int, str] = {1: "employee", **{v: k for k, v in CONTACT_TYPES.items()}, LEAD_TYPE: "lead"}

LIMIT_SCHEMA: dict[str, Any] = {"type": "integer", "minimum": 1, "maximum": 100, "default": 25}
CURSOR_SCHEMA: dict[str, Any] = {"type": "string", "description": "next_cursor from the previous call."}
DATE_SCHEMA: dict[str, Any] = {"type": "string", "format": "date", "description": "YYYY-MM-DD."}


async def call(ctx: ToolContext, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST `api/<path>` like the panel does and return the answer; the app's error answers raise ToolError."""
    body = await api(ctx, path, {**_BASE, **_zone(ctx), **(payload or {})})
    if str(body.get("need_logout")) == "1":
        raise AuthExpiredError("The app signed this account out. Reconnect it in the console.")
    message = str(body.get("message") or "")
    if message.startswith("Cannot POST"):
        raise ToolError("Contractor Foreman did not accept this request.", ErrorCode.TARGET_ERROR)
    status = body.get("statusCode")
    if body.get("success") in (False, 0, "0") or (isinstance(status, int) and status >= 400):
        if status in (404, 406) or "not available" in message.lower():
            raise ToolError("Contractor Foreman did not find that record.", ErrorCode.TARGET_ERROR)
        if status in (400, 422) and message:
            raise ToolError(f"Contractor Foreman refused it: {message.replace('..', '; ')}", ErrorCode.TARGET_ERROR)
        raise ToolError("Contractor Foreman could not do this. Try again later.", ErrorCode.TARGET_ERROR)
    return body


def page(args: dict[str, Any]) -> tuple[int, int]:
    """(start, limit) from `cursor` and `limit`."""
    raw = args.get("cursor") or "0"
    if not str(raw).isdigit():
        raise ToolError("cursor must be the next_cursor value from the previous call.", ErrorCode.INVALID_INPUT)
    return int(raw), clamp_limit(args, 25, 100)


def next_cursor(start: int, size: int, got: int) -> str | None:
    return str(start + size) if got >= size else None


def text(value: Any) -> str | None:
    """App text: HTML entities decoded, empty as None."""
    if value is None:
        return None
    out = html.unescape(str(value)).strip()
    return out or None


def num(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "", "0", 0) else None
    except (TypeError, ValueError):
        return None


def money(cents: Any) -> float | None:
    """The app keeps amounts in cents, as text."""
    if cents in (None, ""):
        return None
    try:
        return round(float(cents) / 100, 2)
    except (TypeError, ValueError):
        return None


def to_cents(amount: float) -> int:
    return round(amount * 100)


async def date_format(ctx: ToolContext) -> str:
    """The account's date format (strftime), cached for an hour."""
    cached = await ctx.cache_get("date_format")
    if cached:
        return cached
    body = await call(ctx, "global/settings")
    fmt = str(((body.get("data") or {}).get("app_settings") or {}).get("date_format") or "%m/%d/%Y")
    await ctx.cache_set("date_format", fmt, 3600)
    return fmt


def iso(value: Any, fmt: str) -> str | None:
    """An app date (account format, ISO timestamp or YYYY-MM-DD) as YYYY-MM-DD; empty and zero dates as None."""
    raw = str(value or "").strip()
    if not raw or raw.startswith("00"):
        return None
    try:
        return datetime.strptime(raw, fmt).replace(tzinfo=UTC).date().isoformat()
    except ValueError:
        pass
    try:
        return date.fromisoformat(raw[:10]).isoformat()
    except ValueError:
        return raw


def app_date(value: str, fmt: str) -> str:
    """YYYY-MM-DD from the input in the account's format, as the panel's forms send it."""
    try:
        return date.fromisoformat(value).strftime(fmt)
    except ValueError as exc:
        raise ToolError(f"{value} is not a YYYY-MM-DD date.", ErrorCode.INVALID_INPUT) from exc


async def statuses(ctx: ToolContext, category: str) -> list[dict[str, Any]]:
    """The company's status list for a category (`work_order_status`, ...): key, id, name. Cached 10 min."""
    key = f"status:{category}"
    cached = await ctx.cache_get(key)
    if cached:
        return json.loads(cached)
    body = await call(ctx, "common/get-status-list", {"types": [category]})
    rows = ((body.get("data") or {}).get(category)) or []
    out = [
        {"key": r.get("key"), "id": r.get("type_id"), "name": text(r.get("display_name") or r.get("name"))}
        for r in rows
    ]
    await ctx.cache_set(key, json.dumps(out), 600)
    return out


async def status_id(ctx: ToolContext, category: str, wanted: str) -> int:
    """A status id from its name ("Completed") or key ("wo_completed"), as the company names it."""
    rows = await statuses(ctx, category)
    needle = wanted.strip().lower()
    for row in rows:
        if needle in (str(row["key"]).lower(), str(row["name"] or "").lower()):
            return int(row["id"])
    names = ", ".join(str(r["name"]) for r in rows)
    raise ToolError(f"Unknown status {wanted!r}. Use one of: {names}.", ErrorCode.INVALID_INPUT)


def first_record(body: dict[str, Any]) -> dict[str, Any]:
    """`data` of a detail answer, unwrapping the `data.data` some modules use."""
    data = body.get("data") or {}
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        return data["data"]
    return data if isinstance(data, dict) else {}


def rows(body: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    """The list in a list answer: `data`, or `data.<key>` for modules that wrap it."""
    data = body.get("data")
    for key in keys:
        if isinstance(data, dict) and isinstance(data.get(key), list):
            return data[key]
    return data if isinstance(data, list) else []


async def my_user_id(ctx: ToolContext) -> int:
    """The signed-in user's directory id (get-app-data, the whoami call), cached for an hour."""
    cached = await ctx.cache_get(f"user_id:{ctx.profile.browser_id}")
    if cached:
        return int(cached)
    body = await call(ctx, "get-app-data")
    user_id = int((((body.get("data") or {}).get("user") or {}).get("data") or {}).get("user_id") or 0)
    if not user_id:
        raise ToolError("Contractor Foreman did not say who is signed in.", ErrorCode.TARGET_ERROR)
    await ctx.cache_set(f"user_id:{ctx.profile.browser_id}", str(user_id), 3600)
    return user_id


def created_id(body: dict[str, Any], key: str) -> int:
    """The new record's id from an add answer (`data.<key>`)."""
    value = num((body.get("data") or {}).get(key))
    if value is None:
        raise ToolError("Contractor Foreman did not return the new record.", ErrorCode.TARGET_ERROR)
    return value
