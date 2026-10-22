#!/usr/bin/env python3
"""Turn a site note into today's Contractor Foreman daily log, after checking the day is not logged yet.

    python add_daily_log.py --project-id 1678164 --notes "Framed second floor east wall." --people "Framing crew=4" "Brightline Electric=1"
    python add_daily_log.py --project-id 1678164 --date 2026-10-09 --notes-file note.txt --delivered "48 sheets 1/2 in drywall" --weather-delay "Rain stopped work at 2:30."

Contractor Foreman records the weather for the date and address itself. --dry-run prints the log without saving.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from contractor_foreman_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--project-id", required=True, help="project_id from export_projects.py")
    parser.add_argument("--date", default=date.today().isoformat(), help="Log date, YYYY-MM-DD (default: today)")
    notes = parser.add_mutually_exclusive_group(required=True)
    notes.add_argument("--notes", help="Work done and site notes")
    notes.add_argument("--notes-file", help="Read the notes from this text file")
    parser.add_argument("--arrival", help="Arrival on site, e.g. 07:00")
    parser.add_argument("--departure", help="Departure, e.g. 15:30")
    parser.add_argument("--people", nargs="*", default=[], help='Crews as "name=headcount"')
    parser.add_argument("--delivered", nargs="*", default=[], help="Materials delivered, one argument each")
    parser.add_argument("--weather-notes")
    parser.add_argument("--weather-delay", help="What the weather delayed")
    parser.add_argument("--force", action="store_true", help="Save even when the day already has a log")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    log = {
        "project_id": args.project_id,
        "date": args.date,
        "notes": args.notes or Path(args.notes_file).read_text(encoding="utf-8").strip(),
        "arrival_time": args.arrival,
        "departure_time": args.departure,
        "people": {name: int(count) for name, _, count in (p.partition("=") for p in args.people)} or None,
        "materials_delivered": args.delivered or None,
        "weather_notes": args.weather_notes,
        "weather_delay": args.weather_delay,
    }
    existing = call("list_daily_logs", {"project_id": args.project_id, "from": args.date, "to": args.date})
    if existing["daily_logs"] and not args.force:
        ids = ", ".join(row["daily_log_id"] for row in existing["daily_logs"])
        raise SystemExit(f"{args.date} already has a log on this project ({ids}). Pass --force to add another.")
    if args.dry_run:
        print(json.dumps({k: v for k, v in log.items() if v is not None}, indent=2))
        return
    saved = call("create_daily_log", log)
    print(f"Saved daily log {saved['daily_log_id']}: {saved['project_name']}, {saved['date']}")


if __name__ == "__main__":
    run(main)
