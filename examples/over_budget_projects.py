#!/usr/bin/env python3
"""Find Contractor Foreman projects whose actual cost runs past the estimate, with the cost codes behind it.

    python over_budget_projects.py
    python over_budget_projects.py --threshold 10 --out over-budget.csv

Reads job costing (bills, expenses, time cards, equipment) for every open project. --threshold is the
percent over the estimated cost a cost code needs to be listed.
"""

from __future__ import annotations

import argparse

from contractor_foreman_api_mcp.scripting import call, paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--threshold", type=float, default=0, help="Percent over estimate to report (default 0)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = []
    for project in paginate("list_projects", {"limit": 100}, "projects"):
        costing = call("get_job_costing", {"project_id": project["project_id"]})
        for code in costing["cost_codes"]:
            estimated, actual = code["estimated_cost"] or 0, code["actual_cost"] or 0
            if actual <= estimated * (1 + args.threshold / 100) or actual == 0:
                continue
            rows.append(
                {
                    "project": project["name"],
                    "project_id": project["project_id"],
                    "cost_code": f"{code['code'] or ''} {code['name'] or ''}".strip(),
                    "estimated_cost": estimated,
                    "actual_cost": actual,
                    "over_by": round(actual - estimated, 2),
                    "over_percent": round((actual - estimated) / estimated * 100, 1) if estimated else None,
                }
            )
    write_rows(sorted(rows, key=lambda r: -r["over_by"]), args.out)


if __name__ == "__main__":
    run(main)
