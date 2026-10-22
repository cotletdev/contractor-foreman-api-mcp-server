"""Get project: one project's details and contract figures, as the project's Summary and Details tabs show them."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._projects_common import iso, money, number, panel, text
from contractor_foreman_api_mcp.core.errors import ErrorCode, ToolError
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

PROJECT_ID = {"type": "string", "pattern": "^[0-9]+$", "description": "project_id from list_projects."}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"project_id": PROJECT_ID},
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "project_id": "1678216",
    "number": "HR-1001",
    "name": "Kitchen remodel - Oak St",
    "description": "Full kitchen remodel: new cabinets, quartz counters, tile backsplash, LVP flooring.",
    "status": "started",
    "status_name": "Started",
    "type": "Residential",
    "customer": {"id": "6819084", "name": "John Pence", "company": "Fairfield Homes", "phone": "(410) 555-1220"},
    "address": {"street": "412 Oak St", "street2": None, "city": "Raleigh", "state": "NC", "zip": "27601"},
    "site_manager": "Arthur Christian",
    "project_manager": None,
    "start_date": "2026-10-26",
    "end_date": "2026-12-18",
    "completion_date": None,
    "original_contract_amount": 65264.4,
    "approved_change_orders": 1093.75,
    "revised_contract_amount": 66358.15,
    "budgeted_cost": 49219.0,
    "committed_cost": 36304.63,
    "actual_cost": 8001.0,
    "invoiced": 46959.33,
    "paid": 15668.89,
    "outstanding_invoices": 26703.87,
    "retainage_held": 4586.57,
    "retainage_percent": 10.0,
    "percent_complete": 39.0,
}


def project_detail(data: dict[str, Any]) -> dict[str, Any]:
    original = money(data.get("original_contract_amount"))
    approved_co = money(data.get("approved_co_total"))
    return {
        "project_id": str(data.get("id")),
        "number": text(data.get("project_id")),
        "name": text(data.get("project_name")),
        "description": text(data.get("description")),
        "status": data.get("project_status_key") or data.get("project_status"),
        "status_name": text(data.get("project_status_name")),
        "type": text(data.get("project_type_name")),
        "customer": {
            "id": str(data.get("customer_id") or "") or None,
            "name": text(data.get("customer_name_only")) or text(data.get("customer_name")),
            "company": text(data.get("customer_company")),
            "phone": text(data.get("customer_contact_phone")) or text(data.get("cust_phone")),
        },
        "address": {
            "street": text(data.get("address1")),
            "street2": text(data.get("address2")),
            "city": text(data.get("city")),
            "state": text(data.get("state")),
            "zip": text(data.get("zip")),
        },
        "site_manager": text(data.get("site_manager_name_only")),
        "project_manager": text(data.get("project_manager_name_only")),
        "start_date": iso(data.get("start_date")),
        "end_date": iso(data.get("end_date")),
        "completion_date": iso(data.get("completion_date")),
        "original_contract_amount": original,
        "approved_change_orders": approved_co,
        "revised_contract_amount": round(original + approved_co, 2),
        "budgeted_cost": money(data.get("budgeted")),
        "committed_cost": money(data.get("commited")),
        "actual_cost": money(data.get("actual")),
        "invoiced": money(data.get("invoiced")),
        "paid": money(data.get("paid_amount")),
        "outstanding_invoices": money(data.get("outstanding_invoice_total")),
        "retainage_held": money(data.get("contract_amount_held")),
        "retainage_percent": number(data.get("retention")),
        "percent_complete": round(number(data.get("progress")) * 100, 1),
    }


async def read_project(ctx: ToolContext, project_id: str) -> dict[str, Any]:
    """The raw `projects/get-details` record (never returned as is: it holds staff contact data)."""
    body = await panel(ctx, "projects/get-details", {"project_id": int(project_id), "record_type": "project"})
    data = body.get("data")
    if not isinstance(data, dict) or not data.get("id"):
        raise ToolError(
            f"No project {project_id} in this account. Use a project_id from list_projects.", ErrorCode.TARGET_ERROR
        )
    return data


@tool(
    name="get_project",
    title="Get project",
    access="read",
    description="One project: customer, address, stage, dates, contract amounts, costs, billing and retainage.",
    details=(
        "Returns one project. The revised contract amount is the original contract plus approved change "
        "orders, as the project shows it. Costs are budgeted, committed and actual. Billing is invoiced, "
        "paid and outstanding invoices, with retainage held shown apart. Amounts are in dollars. Use "
        "project_id from list_projects."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/{project_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_project(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return project_detail(await read_project(ctx, args["project_id"]))
