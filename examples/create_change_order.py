#!/usr/bin/env python3
"""Write a Contractor Foreman change order from a client request, and email it when you add --send.

    python create_change_order.py --project-id 1678167 --title "Second kitchen window" --item "Window unit,material,1,ea,780" --item "Install labor,labor,6,hr,60" --markup 20 --description "Client request on 9 Oct."
    python create_change_order.py --project-id 1678167 --title "Upgrade to quartz" --request
    python create_change_order.py --send 540713

An --item is "name,type,quantity,unit,unit_cost". --request saves a change order request (COR) to price first.
"""

from __future__ import annotations

import argparse
from typing import Any

from contractor_foreman_api_mcp.scripting import call, run


def parse_item(text: str, markup: float | None) -> dict[str, Any]:
    name, kind, quantity, unit, cost = (part.strip() for part in text.split(","))
    item: dict[str, Any] = {
        "name": name,
        "type": kind,
        "quantity": float(quantity),
        "unit": unit,
        "unit_cost": float(cost),
    }
    if markup is not None:
        item["markup_percent"] = markup
    return item


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--project-id")
    parser.add_argument("--title")
    parser.add_argument("--item", action="append", default=[], help='"name,type,quantity,unit,unit_cost"')
    parser.add_argument("--markup", type=float, help="Markup percent on every item")
    parser.add_argument("--description", help="Who asked, when, what")
    parser.add_argument("--request", action="store_true", help="Save as a change order request")
    parser.add_argument("--send", metavar="CHANGE_ORDER_ID", help="Email this saved change order to the customer")
    args = parser.parse_args()

    if args.send:
        sent = call("send_change_order", {"change_order_id": args.send})
        print(f"Sent to {', '.join(sent['sent_to'])}: {sent['subject']}")
        return
    if not args.project_id or not args.title:
        parser.error("--project-id and --title are required, or pass --send CHANGE_ORDER_ID")
    params = {
        "project_id": args.project_id,
        "title": args.title,
        "items": [parse_item(item, args.markup) for item in args.item] or None,
        "description": args.description,
        "kind": "request" if args.request else None,
    }
    order = call("create_change_order", params)
    print(
        f"{order['kind']} {order['change_order_id']} (#{order['number']}) on {order['project_name']}: total {order['total']:,.2f}"
    )
    print(f"Check it, then email it with: python create_change_order.py --send {order['change_order_id']}")


if __name__ == "__main__":
    run(main)
