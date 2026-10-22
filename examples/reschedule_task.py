#!/usr/bin/env python3
"""Move a schedule task by N days and every task that waits on it, keeping their lengths.

    python reschedule_task.py --project-id 1678164 --task "Rough In Plumbing" --days 5 --dry-run
    python reschedule_task.py --project-id 1678164 --task task_7570477 --days -2

Follows the schedule's dependencies (finish to start and the rest) from the task you name.
Without --dry-run every move is saved in the Contractor Foreman schedule.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Any

from contractor_foreman_api_mcp.scripting import call, run


def find(tasks: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for task in tasks:
        if key in (task["task_id"], task["name"]):
            return task
    raise SystemExit(f"No task {key!r}. Names: {', '.join(t['name'] for t in tasks)}")


def downstream(tasks: list[dict[str, Any]], start: str) -> list[dict[str, Any]]:
    """The task and everything that depends on it, directly or not, in order."""
    order, queue = [start], [start]
    while queue:
        current = queue.pop(0)
        for task in tasks:
            deps = {d["task_id"] for d in task.get("depends_on") or []}
            if current in deps and task["task_id"] not in order:
                order.append(task["task_id"])
                queue.append(task["task_id"])
    by_id = {t["task_id"]: t for t in tasks}
    return [by_id[i] for i in order]


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--task", required=True, help="task_id or exact task name")
    parser.add_argument("--days", type=int, required=True, help="Days to move, negative for earlier")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tasks = call("list_schedule_tasks", {"project_id": args.project_id})["tasks"]
    for task in downstream(tasks, find(tasks, args.task)["task_id"]):
        if not task.get("start_date"):
            continue
        new_start = (date.fromisoformat(task["start_date"]) + timedelta(days=args.days)).isoformat()
        print(f"{task['name']}: {task['start_date']} -> {new_start}")
        if not args.dry_run:
            call(
                "update_schedule_task",
                {"project_id": args.project_id, "task_id": task["task_id"], "start_date": new_start},
            )


if __name__ == "__main__":
    run(main)
