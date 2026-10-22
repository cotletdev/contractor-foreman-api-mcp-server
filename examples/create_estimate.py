#!/usr/bin/env python3
"""Build a Contractor Foreman estimate from a scope list in CSV, print the total, and email it if you say so.

    python create_estimate.py --project-id 1678216 --title "Johnson bathroom remodel" --items scope.csv --markup 20
    python create_estimate.py --project-id 1678216 --title "Johnson bathroom remodel" --items scope.csv --send --message "Here is the estimate we discussed."

scope.csv has the columns name, type (material, labor, equipment, subcontractor, other), quantity, unit,
unit_cost and an optional markup_percent. --markup applies to rows without their own markup.
The estimate is saved first; --send emails its PDF to the project's customer.
"""

from __future__ import annotations

import argparse
import csv
from typing import Any

from contractor_foreman_api_mcp.scripting import call, run


def read_items(path: str, markup: float | None) -> list[dict[str, Any]]:
    items = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            item: dict[str, Any] = {"name": row["name"].strip(), "unit_cost": float(row["unit_cost"])}
            if row.get("type"):
                item["type"] = row["type"].strip()
            if row.get("quantity"):
                item["quantity"] = float(row["quantity"])
            if row.get("unit"):
                item["unit"] = row["unit"].strip()
            if row.get("markup_percent"):
                item["markup_percent"] = float(row["markup_percent"])
            elif markup is not None:
                item["markup_percent"] = markup
            items.append(item)
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--items", required=True, help="CSV file with the scope lines")
    parser.add_argument("--markup", type=float, help="Markup percent for rows without their own")
    parser.add_argument("--description", help="Scope text shown on the estimate")
    parser.add_argument("--exclusions")
    parser.add_argument("--send", action="store_true", help="Email the PDF to the customer after saving")
    parser.add_argument("--message", help="Email text above the PDF")
    args = parser.parse_args()

    params = {
        "project_id": args.project_id,
        "title": args.title,
        "items": read_items(args.items, args.markup),
        "description": args.description,
        "exclusions": args.exclusions,
    }
    estimate = call("create_estimate", params)
    print(
        f"Estimate {estimate['estimate_id']} (#{estimate['number']}): {len(estimate['items'])} items, total {estimate['total']:,.2f}"
    )
    if args.send:
        sent = call("send_estimate", {"estimate_id": estimate["estimate_id"], "message": args.message})
        print(f"Sent to {', '.join(sent['sent_to'])}: {sent['subject']}")


if __name__ == "__main__":
    run(main)
