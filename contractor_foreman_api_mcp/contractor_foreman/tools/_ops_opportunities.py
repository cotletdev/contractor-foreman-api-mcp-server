"""Opportunity shape shared by the opportunity tools. Opportunities are project records with type "opportunity"."""

from __future__ import annotations

from typing import Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import iso, money, num, text

STAGES = ["received", "pending", "qualifying", "qualified", "quoted", "awarded", "lost"]

EXAMPLE_OPPORTUNITY: dict[str, Any] = {
    "opportunity_id": 1678221,
    "number": "BP-PATIO",
    "name": "Burger Palace - Patio Enclosure",
    "customer_id": 6819060,
    "customer": "Barry Sizemore (Burger Palace)",
    "stage": "qualifying",
    "score": 4,
    "budget": 48000.0,
    "est_sales_date": "2026-12-15",
    "project_type": "Commercial",
    "referral_source": None,
    "assigned_to": "Michael Howard",
    "description": None,
    "address": {"address1": None, "city": None, "state": None, "zip": None},
    "added_on": "2026-10-21",
}


def opportunity_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "opportunity_id": num(row.get("id")),
        "number": text(row.get("project_id")),
        "name": text(row.get("project_name")),
        "customer_id": num(row.get("customer_id")),
        "customer": text(row.get("customer_name")),
        "stage": (text(row.get("stage_key") or row.get("stage")) or "").removeprefix("opportunity_stage_") or None,
        "score": num(row.get("score")),
        "budget": money(row.get("budget_amount")),
        "est_sales_date": iso(row.get("est_sales_date"), fmt),
        "project_type": text(row.get("project_type_name")),
        "referral_source": text(row.get("referral_source_name")),
        "assigned_to": text(row.get("assignee_name")),
        "description": text(row.get("description")),
        "address": {
            "address1": text(row.get("address1")),
            "city": text(row.get("city")),
            "state": text(row.get("state")),
            "zip": text(row.get("zip")),
        },
        "added_on": iso(row.get("date_added"), fmt),
    }
