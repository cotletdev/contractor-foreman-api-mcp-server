#!/usr/bin/env python3
"""List Contractor Foreman invoices that are past due with a balance, oldest first, with days overdue.

    python overdue_invoices.py
    python overdue_invoices.py --out overdue.csv
    python overdue_invoices.py --project-id 1678164

Good as a Monday cron job. Only submitted or on-hold invoices with a balance due count.
"""

from __future__ import annotations

import argparse
from datetime import date

from contractor_foreman_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--project-id", help="Only this project's invoices")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    today = date.today()
    params = {"unpaid_only": True, "due_before": today.isoformat(), "limit": 100}
    if args.project_id:
        params["project_id"] = args.project_id
    rows = [
        {
            "number": inv["number"],
            "customer": inv["customer_name"],
            "project": inv["project_name"],
            "due_date": inv["due_date"],
            "days_overdue": (today - date.fromisoformat(inv["due_date"])).days,
            "balance_due": inv["balance_due"],
            "invoice_id": inv["invoice_id"],
        }
        for inv in paginate("list_invoices", params, "invoices")
        if inv.get("due_date")
    ]
    rows.sort(key=lambda r: -r["days_overdue"])
    write_rows(rows, args.out)
    if rows:
        print(f"{len(rows)} overdue, {sum(r['balance_due'] or 0 for r in rows):,.2f} outstanding")


if __name__ == "__main__":
    run(main)
