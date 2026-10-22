"""Shapes shared by the work order, service ticket, RFI, submittal and inspection tools (recorded 21.10.2026)."""

from __future__ import annotations

from typing import Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import iso, money, num, text

RFI_TYPE = 124  # correspondence type of an RFI; the same module also keeps schedule and compliance notices

WORK_ORDER_STATUSES = ["open", "estimating", "submitted", "approved", "canceled", "completed"]
WORK_ORDER_KEYS = dict(
    zip(
        WORK_ORDER_STATUSES,
        ["wo_open", "wo_bidding", "wo_pending", "wo_approved", "wo_cancelled", "wo_completed"],
        strict=True,
    )
)
TICKET_STATUSES = [
    "unscheduled",
    "scheduled",
    "en_route",
    "checked_in",
    "requires_followup",
    "canceled",
    "completed",
    "closed",
]
TICKET_KEYS = {s: f"ticket_status_{'cancelled' if s == 'canceled' else s}" for s in TICKET_STATUSES}


def work_order_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "work_order_id": num(row.get("work_order_id")),
        "number": text(row.get("prefix_company_work_order_id") or row.get("company_order_id")),
        "subject": text(row.get("subject")),
        "description": text(row.get("description")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "customer_id": num(row.get("customer_id")),
        "customer": text(row.get("customer_name")),
        "status": text(row.get("work_order_status_name")),
        "start_date": iso(row.get("order_date"), fmt),
        "end_date": iso(row.get("end_date"), fmt),
        "total": money(row.get("total")),
        "assigned_to": text(row.get("assignee_name")),
        "issued_by": text(row.get("issued_by_name")),
    }


def _names(value: Any) -> str | None:
    """Technicians: a name list as text in lists, a list of people in the detail answer."""
    if isinstance(value, list):
        names = [text(p.get("display_name")) for p in value if isinstance(p, dict)]
        return ", ".join(n for n in names if n) or None
    return text(value)


def ticket_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "service_ticket_id": num(row.get("service_ticket_id")),
        "number": text(row.get("company_ticket_id")),
        "title": text(row.get("title")),
        "description": text(row.get("description")),
        "status": text(row.get("job_status_name")),
        "customer_id": num(row.get("customer_id")),
        "customer": text(row.get("customer_name")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "service_date": iso(row.get("service_format_date") or row.get("service_date_only"), fmt),
        "service_time": text(row.get("service_time")),
        "technicians": _names(row.get("service_technicians")) or text(row.get("service_tech_name")),
    }


def rfi_out(row: dict[str, Any], fmt: str, status_names: dict[int, str]) -> dict[str, Any]:
    return {
        "rfi_id": num(row.get("correspondence_id")),
        "number": text(row.get("custom_correspondence_id") or row.get("company_correspondence_id")),
        "title": text(row.get("rfi_title")) or text(row.get("reference_area_of_question")),
        "question": text(row.get("info_request")),
        "reference_area": text(row.get("reference_area_of_question")),
        "plan_sheet": text(row.get("plan_sheet_no")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "date": iso(row.get("correspondence_date"), fmt),
        "response_needed_by": iso(row.get("response_needed_by"), fmt),
        "response_received": iso(row.get("response_received"), fmt),
        "answer": text(row.get("resolution_notes")),
        "status": status_names.get(num(row.get("rfi_status")) or 0),
    }


def submittal_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "submittal_id": num(row.get("submittal_id")),
        "number": text(row.get("prefix_company_submittal_id") or row.get("company_submittal_id")),
        "title": text(row.get("title")),
        "project_id": num(row.get("project_primary_id") or row.get("project_id")),
        "project": text(row.get("project_name")),
        "status": text(row.get("status_name")),
        "date_received": iso(row.get("date_received"), fmt),
        "due_date": iso(row.get("due_date"), fmt),
        "assigned_to": text(row.get("assignee_name")),
        "approved_by": text(row.get("external_approved_by_name")),
    }


def inspection_out(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    return {
        "inspection_id": num(row.get("inspection_id")),
        "number": text(row.get("custom_inspection_id") or row.get("company_inspection_id")),
        "type": text(row.get("inspection_type")),
        "project_id": num(row.get("project_id")),
        "project": text(row.get("project_name")),
        "date": iso(row.get("inspection_date"), fmt),
        "time": text(row.get("inspection_time")),
        "status": text(row.get("inspection_status_name")),
        "agency": text(row.get("inspection_agency_name")),
        "inspected_by": text(row.get("inspected_by")),
        "permit_number": text(row.get("permit_number")),
        "assigned_to": text(row.get("assigned_to_name")),
        "notes": text(row.get("notes")),
    }
