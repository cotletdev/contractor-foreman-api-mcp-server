"""Project note shape (the Notes tab of a project: common notes on module key "projects")."""

from __future__ import annotations

from typing import Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import num, text

EXAMPLE_NOTE: dict[str, Any] = {
    "note_id": 4352070,
    "title": "Grease trap location",
    "text": "Owner approved moving the grease trap 18 inches east of the prep sink. Plumber notified on site.",
    "added_by": "Sam Ortega",
    "added_on": "10/21/2026 08:03 AM",
    "files": 0,
}


def note_out(row: dict[str, Any]) -> dict[str, Any]:
    added = " ".join(p for p in (text(row.get("date_added")), text(row.get("time_added"))) if p)
    return {
        "note_id": num(row.get("note_id")),
        "title": text(row.get("title")),
        "text": text(row.get("description")),
        "added_by": text(row.get("added_by")),
        "added_on": added or None,
        "files": len(row.get("aws_files") or []),
    }
