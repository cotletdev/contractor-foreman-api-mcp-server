"""Shared calls and conversions for the project, schedule, daily log, punchlist and to-do tools.

Every call goes through `client.api` (sign-out on HTTP 200 is caught there). The panel adds `version`,
`from` and `force_login` to every body (`web-worker` helper, 21.10.2026); `panel` does the same and turns
the app's in-body errors into `ToolError`s.
"""

from __future__ import annotations

import html
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.client import api
from contractor_foreman_api_mcp.core.errors import AuthExpiredError, ErrorCode, ToolError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

_BASE = {"version": "web", "from": "panel", "force_login": 0}


async def panel(ctx: ToolContext, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST one panel call with the panel's base fields; returns the body, raises on an app error."""
    body = await api(ctx, path, {**_BASE, **(payload or {})})
    if str(body.get("need_logout") or "") == "1":
        raise AuthExpiredError("The app signed this account out. Sign in again in Chrome, then run connect.")
    message = str(body.get("message") or "")
    if message.startswith("Cannot POST"):
        raise ToolError("Contractor Foreman no longer answers this request.", ErrorCode.TARGET_ERROR)
    status = body.get("statusCode")
    if body.get("success") is False or (isinstance(status, int) and not 200 <= status <= 205):
        if status in (404, 406, 400) or "not available" in message.lower():
            raise ToolError(f"Contractor Foreman: {message or 'record not found'}", ErrorCode.TARGET_ERROR)
        if status == 422:
            raise ToolError(f"Contractor Foreman refused it: {message.replace('..', '.')}", ErrorCode.TARGET_ERROR)
        raise ToolError("Contractor Foreman could not do it right now. Try again later.", ErrorCode.TARGET_ERROR)
    return body


def money(cents: Any) -> float:
    """Project amounts are whole cents in strings ("6635815" is $66,358.15)."""
    return round(number(cents) / 100, 2)


def number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def iso(value: Any) -> str | None:
    """The app's dates ("10/26/2026", "26/Oct/2026", "2026-10-26 00:00:00") as YYYY-MM-DD."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    for fmt in ("%m/%d/%Y", "%d/%b/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_date(value: str, field: str) -> date:
    """An input date (YYYY-MM-DD), or INVALID_INPUT naming the field."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ToolError(f"{field} must be a date like 2026-10-26.", ErrorCode.INVALID_INPUT) from None


def mdy(value: str, field: str) -> str:
    """An input date as the app's form format MM/DD/YYYY."""
    return parse_date(value, field).strftime("%m/%d/%Y")


def time_24(value: str, field: str) -> str:
    """An input time ("7:30", "07:30", "7:30 AM") as HH:MM, 24-hour."""
    text = value.strip().upper()
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    raise ToolError(f"{field} must be a time like 07:30 or 3:30 PM.", ErrorCode.INVALID_INPUT)


def day_after(value: date) -> date:
    return value + timedelta(days=1)


def compact(values: dict[str, Any]) -> dict[str, Any]:
    """Drop empty strings and None: the app's validators refuse empty optional fields."""
    return {key: value for key, value in values.items() if value is not None and value != ""}


def text(value: Any) -> str | None:
    """A text field with the app's HTML entities decoded, None when empty."""
    if value is None:
        return None
    result = html.unescape(str(value)).strip()
    return result or None
