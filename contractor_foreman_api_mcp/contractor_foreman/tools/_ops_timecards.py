"""Time card shapes shared by the time card tools (Time Cards module, recorded 21.10.2026)."""

from __future__ import annotations

from typing import Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import iso, num, text


def hours(value: Any) -> float | None:
    """ "20:30 Hrs" or "20:30" as 20.5; "Running" and empty as None."""
    raw = str(value or "").replace("Hrs", "").strip()
    if ":" not in raw:
        return None
    h, _, m = raw.partition(":")
    try:
        return round(int(h) + int(m) / 60, 2)
    except ValueError:
        return None


def minutes_to_hours(value: Any) -> float:
    try:
        return round(int(value or 0) / 60, 2)
    except (TypeError, ValueError):
        return 0.0


def timecard_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    running = str(row.get("timecard_status")) != "stop"
    return {
        "timecard_id": num(row.get("timecard_id")),
        "type": text(row.get("type")),
        "employee": text(row.get("employee")),
        "crew": text(row.get("crew_names")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "date": iso(row.get("clock_in_date"), fmt),
        "clock_in": text(row.get("clock_in_time")),
        "clock_out": None if running else text(row.get("clock_out_time")),
        "clock_out_date": None if running else iso(row.get("clock_out_date"), fmt),
        "running": running,
        "hours": None if running else hours(row.get("hours_worked")),
        "break_hours": hours(row.get("break_hours")),
        "notes": text(row.get("notes")),
    }


EXAMPLE_TIMECARD: dict[str, Any] = {
    "timecard_id": 13199473,
    "type": "employee",
    "employee": "Sam Ortega",
    "crew": None,
    "project_id": 1678164,
    "project": "Speedway - Tenant Fit Out",
    "date": "2024-01-31",
    "clock_in": "09:16 AM",
    "clock_out": "05:16 AM",
    "clock_out_date": "2024-02-01",
    "running": False,
    "hours": 20.0,
    "break_hours": 0.0,
    "notes": None,
}
