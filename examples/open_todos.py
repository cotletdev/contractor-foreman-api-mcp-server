#!/usr/bin/env python3
"""Open Contractor Foreman to-dos that are due soon or late, grouped by project, for a morning check.

python open_todos.py
python open_todos.py --days 3 --out todos.csv
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from contractor_foreman_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--days", type=int, default=7, help="Due within this many days, late ones included")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    until = (date.today() + timedelta(days=args.days)).isoformat()
    rows = [
        {k: todo.get(k) for k in ("project_name", "name", "priority", "due_date", "status", "todo_id")}
        for todo in paginate("list_todos", {"limit": 100}, "todos")
        if todo["status"] != "complete" and todo.get("due_date") and todo["due_date"] <= until
    ]
    rows.sort(key=lambda r: (r["project_name"] or "", r["due_date"]))
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
