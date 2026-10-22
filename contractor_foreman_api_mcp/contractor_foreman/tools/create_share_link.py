"""Create share link: a short internal link to an estimate, change order or invoice (common/generate-share-link)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._finance_common import share_link
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "record_type": {"type": "string", "enum": ["estimate", "change_order", "invoice"]},
        "record_id": {"type": "string", "minLength": 1, "description": "estimate_id, change_order_id or invoice_id."},
    },
    "required": ["record_type", "record_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "record_type": "estimate",
    "record_id": "1616575",
    "url": "https://app.contractorforeman.net/share/da0a5f746ef95729",
}


@tool(
    name="create_share_link",
    title="Create share link",
    access="write",
    description="Makes a short internal link that opens an estimate, change order or invoice for your signed-in team.",
    details=(
        "The panel's Share Internal Link: a short URL that opens the record in the Contractor Foreman app. "
        "Only people who sign in to your Contractor Foreman company can open it. It is not a public page for "
        "the customer. To get a document to the customer, send_estimate, send_change_order and send_invoice "
        "email the PDF."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /share-links",
    example_response=EXAMPLE_RESPONSE,
)
async def create_share_link(ctx: ToolContext, args: dict[str, Any]) -> Any:
    url = await share_link(ctx, args["record_type"], int(args["record_id"]))
    return {"record_type": args["record_type"], "record_id": str(args["record_id"]), "url": url}
