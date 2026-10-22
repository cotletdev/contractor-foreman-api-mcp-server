"""Daily log reading and writing shared by the daily log tools.

A log is created with only project, date and arrival time (`daily-log/add`, camelCase keys, as the panel's
AddDailyLog form). The rest is saved field by field like the Details tab does it: `daily-log/{id}/update`
(work performed, weather and delay notes, departure time, jobsite notes), `daily-log/{id}/update-people`
(crew and visitor notes) and `daily-log/{id}/add-update-materials` (material notes). Recorded 21.10.2026.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import (
    compact,
    iso,
    number,
    panel,
    text,
    time_24,
)
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

# Write inputs shared by create_daily_log and update_daily_log.
WRITE_PROPERTIES: dict[str, Any] = {
    "notes": {"type": "string", "description": "Work done and site notes (the log's Work Performed)."},
    "arrival_time": {"type": "string", "description": "Arrival on site, e.g. 07:00 or 7:00 AM."},
    "departure_time": {"type": "string", "description": "Departure from site, e.g. 15:30."},
    "people": {
        "description": "Crews, subcontractors and visitors on site: headcount per crew, or free text.",
        "oneOf": [
            {"type": "object", "additionalProperties": {"type": ["integer", "string"]}},
            {"type": "string"},
        ],
    },
    "visitors": {"type": "string", "description": "Visitors on site (inspector, owner, architect)."},
    "materials_delivered": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Materials delivered or used, one line each.",
    },
    "weather_notes": {"type": "string", "description": "Your own notes next to the recorded weather."},
    "weather_delay": {"type": "string", "description": "What the weather delayed. Marks a weather delay."},
    "schedule_delay": {"type": "string", "description": "What else held the schedule up. Marks a schedule delay."},
    "jobsite_notes": {"type": "string", "description": "Jobsite condition notes."},
}

EXAMPLE_LOG: dict[str, Any] = {
    "daily_log_id": "2021965",
    "project_id": "1678164",
    "project_name": "Speedway - Tenant Fit Out",
    "date": "2026-10-20",
    "arrival_time": "07:00 AM",
    "departure_time": "03:30 PM",
    "created_by": "Michael Howard",
    "notes": "Hung and taped drywall in the dining area. Patched ceiling at the old soffit.",
    "people": "Drywall crew: 3, Electrician: 1",
    "employees_on_site": [],
    "visitors": "Homeowner walked the site at 11 am.",
    "materials": "30 sheets 1/2 in drywall delivered by ABC Supply.",
    "materials_used": [],
    "equipment_used": [{"name": "Dumpster Trailer", "hours": "8:00", "unit": "DAY"}],
    "weather": {
        "temperature_f": "68/39 °F",
        "temperature_c": "20/4 °C",
        "conditions": ["Partially cloudy", "Rain, Overcast"],
        "notes": "Light rain after 2 pm, work moved inside.",
        "delay": True,
        "delay_notes": "Exterior trim paused at 2 pm.",
    },
    "schedule_delay": None,
    "jobsite_condition": "Good",
    "jobsite_notes": "Site cleaned at end of day.",
}


def people_text(value: Any) -> str | None:
    if isinstance(value, dict):
        return ", ".join(f"{name}: {count}" for name, count in value.items()) or None
    return text(value)


def _conditions(raw: Any) -> list[str]:
    try:
        hours = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        return []
    seen = Counter(text(hour.get("conditions")) for hour in hours or [] if isinstance(hour, dict))
    return [name for name, _ in seen.most_common() if name]


def _hours(value: Any) -> str | None:
    """Equipment hours come as "000008:0"."""
    raw = text(value)
    if not raw or ":" not in raw:
        return raw
    whole, part = raw.split(":", 1)
    return f"{int(whole or 0)}:{int(part or 0):02d}"


def log_view(
    log: dict[str, Any], people: dict[str, Any], materials: dict[str, Any], equipment: dict[str, Any]
) -> dict[str, Any]:
    on_site = (people.get("peopleOnSite") or {}).get("employee_on_site_details") or []
    return {
        "daily_log_id": str(log.get("log_id")),
        "project_id": str(log.get("project_id")),
        "project_name": text(log.get("project_name")),
        "date": iso(log.get("arrival_date")),
        "arrival_time": text(log.get("arrival_time")),
        "departure_time": text(log.get("departure_time")),
        "created_by": text(log.get("employee")),
        "notes": text(log.get("task_performed")),
        "people": text(log.get("emp_work_notes")),
        "employees_on_site": [text(item.get("display_name") or item.get("name")) for item in on_site],
        "visitors": text(log.get("visitors_notes")) if number(log.get("any_visitor_onsite")) else None,
        "materials": text(materials.get("materialNotes")) or text(log.get("material_notes")),
        "materials_used": [
            {
                "name": text(item.get("name") or item.get("item_name")),
                "quantity": item.get("quantity"),
                "unit": text(item.get("unit")),
            }
            for item in materials.get("materialsData") or []
        ],
        "equipment_used": [
            {"name": text(item.get("name")), "hours": _hours(item.get("hours")), "unit": text(item.get("unit"))}
            for item in equipment.get("equipmentsUsed") or []
        ],
        "weather": {
            "temperature_f": text(log.get("weather_temp_f")),
            "temperature_c": text(log.get("weather_temp_c")),
            "conditions": _conditions(log.get("weather_json_f")),
            "notes": text(log.get("weather_notes")),
            "delay": bool(number(log.get("any_weather_delay"))),
            "delay_notes": text(log.get("weather_delay_notes")),
        },
        "schedule_delay": text(log.get("schedule_delay_notes")) if number(log.get("any_schedule_delay")) else None,
        "jobsite_condition": text(log.get("jobsite_condition_name")),
        "jobsite_notes": text(log.get("jobsite_notes")),
    }


async def read_log(ctx: ToolContext, log_id: str) -> dict[str, Any]:
    body = await panel(ctx, f"daily-log/{log_id}", {})
    log = body.get("data")
    if not isinstance(log, dict) or not log.get("log_id"):
        raise ToolError(f"No daily log {log_id} in this account. Use list_daily_logs.", ErrorCode.TARGET_ERROR)
    parts = [
        (await panel(ctx, f"daily-log/{log_id}/{part}", {})).get("data") or {}
        for part in ("get-people", "get-materials", "get-equipments")
    ]
    return log_view(log, *parts)


async def write_fields(ctx: ToolContext, log_id: str, args: dict[str, Any], *, skip_arrival: bool = False) -> None:
    """Save the optional fields of a log, one panel call per section that has something to save."""
    details = compact(
        {
            "taskPerformed": text(args.get("notes")),
            "departureTime": time_24(args["departure_time"], "departure_time") if args.get("departure_time") else None,
            "arrivalTime": None
            if skip_arrival or not args.get("arrival_time")
            else time_24(args["arrival_time"], "arrival_time"),
            "weatherNotes": text(args.get("weather_notes")),
            "jobsiteNotes": text(args.get("jobsite_notes")),
        }
    )
    if args.get("weather_delay"):
        details.update(anyWeatherDelay=1, weatherDelayNotes=text(args["weather_delay"]))
    if args.get("schedule_delay"):
        details.update(anyScheduleDelay=1, scheduleDelayNotes=text(args["schedule_delay"]))
    if details:
        await panel(ctx, f"daily-log/{log_id}/update", details)
    people = compact({"empWorkNotes": people_text(args.get("people"))})
    if args.get("visitors"):
        people.update(anyVisitorOnsite=1, visitorsNotes=text(args["visitors"]))
    if people:
        await panel(ctx, f"daily-log/{log_id}/update-people", people)
    lines = [line.strip() for line in args.get("materials_delivered") or [] if line and line.strip()]
    if lines:
        await panel(ctx, f"daily-log/{log_id}/add-update-materials", {"materialNotes": "\n".join(lines)})
