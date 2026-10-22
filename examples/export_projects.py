#!/usr/bin/env python3
"""Export your Contractor Foreman projects to CSV or JSON: customer, stage, dates, contract, costs, percent complete.

    python export_projects.py --out projects.csv
    python export_projects.py --status started
    python export_projects.py --include-completed --search "Oak St"

Open projects by default, as on the panel's Open tab. Pages are followed automatically.
"""

import argparse

from contractor_foreman_api_mcp.scripting import paginate, run, write_rows

STATUSES = ["pending", "unscheduled", "project_submittal", "bidding", "started", "completed"]


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--status", choices=STATUSES, help="Only projects in this stage")
    parser.add_argument("--include-completed", action="store_true")
    parser.add_argument("--search", help="Match on project name, number or customer")
    parser.add_argument("--max", type=int, help="Stop after this many projects")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    params = {
        "status": args.status,
        "include_completed": args.include_completed or None,
        "search": args.search,
        "limit": 100,
    }
    params = {k: v for k, v in params.items() if v is not None}
    write_rows(list(paginate("list_projects", params, "projects", args.max)), args.out)


if __name__ == "__main__":
    run(main)
