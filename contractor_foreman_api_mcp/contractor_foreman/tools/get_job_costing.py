"""Get job costing: the project's Reports tab, "Job Cost Actual Report" (`projects/labor-report`), summed per cost code.

The report answers line by line, in dollars (not cents like the project record): budgeted lines from the SOV
or the approved estimates and change orders, actual lines from bills, expenses, time cards and equipment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import number, panel, text
from contractor_foreman_api_mcp.contractor_foreman.tools.get_project import PROJECT_ID, read_project
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": PROJECT_ID,
        "budget_from": {
            "type": "string",
            "enum": ["sov", "estimate"],
            "description": "Estimated cost from the Schedule of Values or the approved estimates. Default: the "
            "project's own setting.",
        },
        "labor_rate": {
            "type": "string",
            "enum": ["burden_rate", "emp_wage", "billing_rate", "approved_estimate"],
            "default": "burden_rate",
            "description": "Rate that prices time card hours as labor cost.",
        },
    },
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "project_id": "1678164",
    "budget_from": "sov",
    "cost_codes": [
        {
            "code": "15200-000",
            "name": "Plumbing",
            "group": "Mechanical(15000)",
            "contract_value": 1093.75,
            "estimated_cost": 875.0,
            "actual_cost": 2250.0,
            "difference": -1375.0,
            "actual_by_source": {"bills": 2250.0, "expenses": 0.0, "time_cards": 0.0, "equipment": 0.0},
            "invoiced": 0.0,
        }
    ],
    "totals": {
        "contract_value": 1093.75,
        "estimated_cost": 875.0,
        "actual_cost": 2250.0,
        "difference": -1375.0,
        "invoiced": 0.0,
    },
}

_SOURCES = {
    "bills": "bill_total",
    "expenses": "expense_total",
    "time_cards": "timecard_total",
    "equipment": "equip_labor_total",
}


def _code_name(row: dict[str, Any]) -> tuple[str | None, str]:
    """`cost_code_name` is "Plumbing((15200-000))": the name and the code in double brackets."""
    raw = text(row.get("cost_code_name")) or "Unassigned"
    code = (text(row.get("cost_code")) or "").strip("()") or None
    name = raw.split("((", 1)[0].strip() if "((" in raw else raw
    return code, name


@tool(
    name="get_job_costing",
    title="Get job costing",
    access="read",
    description="Estimated and actual cost per cost code for one project, with the difference and totals.",
    details=(
        "Sums the project's Job Cost Actual report per cost code: contract value, estimated cost (from the "
        "Schedule of Values or the approved estimates, plus change orders), actual cost split into bills, "
        "expenses, time cards and equipment, the difference (estimated minus actual, negative means over) "
        "and the amount invoiced. Time card hours are priced at labor_rate (default burden_rate). Costs with "
        "no cost code are under Unassigned. Amounts are in dollars. Read only."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/{project_id}/job-costing",
    example_response=EXAMPLE_RESPONSE,
)
async def get_job_costing(ctx: ToolContext, args: dict[str, Any]) -> Any:
    project_id = args["project_id"]
    budget_from = args.get("budget_from")
    if not budget_from:
        project = await read_project(ctx, project_id)
        budget_from = "sov" if project.get("budget_is") == "sov" else "estimate"
    body = await panel(
        ctx,
        "projects/labor-report",
        {
            "project_id": project_id,
            "filter_by": "job_cost_actual",
            "generate_from": budget_from,
            "factor_by": args.get("labor_rate") or "burden_rate",
            "show_all": 0,
        },
    )
    rows = (body.get("data") or {}).get("job_cost_actual") or []
    codes: dict[tuple[str | None, str], dict[str, Any]] = {}
    for row in rows:
        code, name = _code_name(row)
        entry = codes.setdefault(
            (code, name),
            {
                "code": code,
                "name": name,
                "group": text(row.get("parent_cost_code_name")),
                "contract_value": 0.0,
                "estimated_cost": 0.0,
                "actual_cost": 0.0,
                "difference": 0.0,
                "actual_by_source": dict.fromkeys(_SOURCES, 0.0),
                "invoiced": 0.0,
            },
        )
        entry["contract_value"] += number(row.get("contract_value"))
        entry["estimated_cost"] += number(row.get("budget_cost"))
        entry["actual_cost"] += number(row.get("total_actual_cost"))
        entry["invoiced"] += number(row.get("invoice_total"))
        for source, key in _SOURCES.items():
            entry["actual_by_source"][source] += number(row.get(key))
    totals = dict.fromkeys(["contract_value", "estimated_cost", "actual_cost", "difference", "invoiced"], 0.0)
    result = []
    for entry in codes.values():
        entry["difference"] = entry["estimated_cost"] - entry["actual_cost"]
        for key in totals:
            totals[key] += entry[key]
        for key in ("contract_value", "estimated_cost", "actual_cost", "difference", "invoiced"):
            entry[key] = round(entry[key], 2)
        entry["actual_by_source"] = {key: round(value, 2) for key, value in entry["actual_by_source"].items()}
        result.append(entry)
    return {
        "project_id": project_id,
        "budget_from": budget_from,
        "cost_codes": result,
        "totals": {key: round(value, 2) for key, value in totals.items()},
    }
