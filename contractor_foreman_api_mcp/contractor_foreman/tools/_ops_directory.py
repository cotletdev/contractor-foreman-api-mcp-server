"""Directory shapes shared by the contact and lead tools (Directory module, recorded 21.10.2026)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import (
    CONTACT_MODULES,
    TYPE_NAMES,
    call,
    next_cursor,
    num,
    page,
    text,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

ADDRESS_PROPS: dict[str, Any] = {
    "address1": {"type": "string", "maxLength": 200},
    "address2": {"type": "string", "maxLength": 200},
    "city": {"type": "string", "maxLength": 100},
    "state": {"type": "string", "maxLength": 50},
    "zip": {"type": "string", "maxLength": 20},
}


def contact_out(row: dict[str, Any]) -> dict[str, Any]:
    """One directory record from the global directory or add-directory answer."""
    kind = num(row.get("orig_type") or row.get("type")) or 0
    out: dict[str, Any] = {
        "contact_id": num(row.get("user_id")),
        "type": TYPE_NAMES.get(kind, text(row.get("type_key")) or str(kind)),
        "name": text(" ".join(p for p in (row.get("first_name") or "", row.get("last_name") or "") if p)),
        "company": text(row.get("company_name") or row.get("company")),
        "display_name": text(row.get("display_name") or row.get("module_display_name")),
        "title": text(row.get("title")),
        "email": text(row.get("email")),
        "phone": text(row.get("phone")),
        "cell": text(row.get("cell")),
        "address": {
            "address1": text(row.get("user_address1") or row.get("address1")),
            "address2": text(row.get("user_address2") or row.get("address2")),
            "city": text(row.get("user_city") or row.get("city")),
            "state": text(row.get("user_state") or row.get("state")),
            "zip": text(row.get("user_zip") or row.get("zip")),
        },
    }
    if kind == 204:
        out["stage"] = (text(row.get("stage")) or "").removeprefix("lead_stage_") or None
        out["quality"] = num(row.get("quality"))
    return out


async def list_directory(ctx: ToolContext, args: dict[str, Any], types: list[int]) -> dict[str, Any]:
    start, size = page(args)
    payload: dict[str, Any] = {
        "filter": {"status": "0"},
        "directory": types,
        "start": start,
        "limit": size,
        "app_users": False,
    }
    if args.get("search"):
        payload["search"] = args["search"].strip()
    body = await call(ctx, "common/get-global-directory", payload)
    found = [r for r in body.get("data") or [] if isinstance(r, dict)]
    return {"contacts": [contact_out(r) for r in found], "next_cursor": next_cursor(start, size, len(found))}


async def add_directory(ctx: ToolContext, kind: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Add a directory record the way the panel's "Add" drawer does, with no app access and no invite."""
    payload = {
        "company_name": "",
        "first_name": "",
        "last_name": "",
        "phone": "",
        "cell": "",
        "email": "",
        "address1": "",
        "address2": "",
        "city": "",
        "state": "",
        "zip": "",
        **{k: v.strip() if isinstance(v, str) else v for k, v in fields.items()},
        "type": kind,
        "module_id": CONTACT_MODULES[kind],
        "isPopupCall": True,
        "access_to_custom_fields": 0,
    }
    if not (payload["company_name"] or payload["first_name"] or payload["last_name"]):
        raise ToolError("Give a first and last name or a company name.", ErrorCode.INVALID_INPUT)
    created = (await call(ctx, "directory/add-directory", payload)).get("data") or {}
    # The add answer leaves out phone and cell; the detail call has the record as saved.
    detail = await call(ctx, "directory/get-directory-details", {"directoryId": created.get("user_id")})
    row = detail.get("data")
    return contact_out(row if isinstance(row, dict) and row.get("user_id") else created)
