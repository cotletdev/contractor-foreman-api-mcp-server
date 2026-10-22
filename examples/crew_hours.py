#!/usr/bin/env python3
"""Crew hours and labor cost per project from Contractor Foreman time cards, per employee.

    python crew_hours.py --days 7
    python crew_hours.py --project-id 1678164 --from 2026-10-01 --to 2026-10-31 --out october.csv

Without --project-id it covers every open project and skips the ones with no hours.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from contractor_foreman_api_mcp.scripting import call, paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--project-id", type=int)
    parser.add_argument("--days", type=int, default=7, help="Last N days (default 7), unless --from is given")
    parser.add_argument("--from", dest="start", help="First day, YYYY-MM-DD")
    parser.add_argument("--to", dest="end", help="Last day, YYYY-MM-DD (default: today)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    end = args.end or date.today().isoformat()
    start = args.start or (date.fromisoformat(end) - timedelta(days=args.days - 1)).isoformat()
    if args.project_id:
        projects = [{"project_id": args.project_id, "name": str(args.project_id)}]
    else:
        projects = list(paginate("list_projects", {"limit": 100}, "projects"))
    rows = []
    for project in projects:
        hours = call(
            "list_project_crew_hours", {"project_id": int(project["project_id"]), "start_date": start, "end_date": end}
        )
        for person in hours["employees"]:
            rows.append({"project": project["name"], **person})
    write_rows(rows, args.out)
    print(f"{start} to {end}: {sum(r['hours'] for r in rows):g} h, labor cost {sum(r['cost'] for r in rows):,.2f}")


if __name__ == "__main__":
    run(main)
