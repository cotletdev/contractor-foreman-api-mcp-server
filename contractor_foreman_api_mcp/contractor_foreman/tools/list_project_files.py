"""List project files: a project's Files tab (photos and documents)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contractor_foreman_api_mcp.contractor_foreman.tools._ops_common import call, num, text
from contractor_foreman_api_mcp.core.tools import tool

if TYPE_CHECKING:
    from contractor_foreman_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"project_id": {"type": "integer", "description": "The project's numeric id (list_projects)."}},
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "files": [
        {
            "file_id": 34315199,
            "name": "2.jpg",
            "title": None,
            "is_image": True,
            "size_bytes": 18708,
            "url": "https://cdn.contractorforeman.net/27272/6819056/demo_data/large/2.jpg?token=...&expires=1795262454",
            "thumbnail_url": (
                "https://cdn.contractorforeman.net/27272/6819056/demo_data/large/2.jpg"
                "?token=...&class=thumb&expires=1795262454"
            ),
            "notes": None,
            "tags": None,
            "added_on": "2026-10-21T10:27:46.000Z",
        }
    ]
}


@tool(
    name="list_project_files",
    title="List project files",
    access="read",
    confirm=False,
    description="Photos and documents on a project, with name, size and a download link.",
    details=(
        "Reads a Contractor Foreman project's Files tab, newest first: file name, title, whether it is an image, "
        "size, notes, tags, when it was added and a download link. The app signs the links and they expire "
        "about 30 days after the call (the expires parameter). Call again for fresh ones."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/{project_id}/files",
    example_response=EXAMPLE_RESPONSE,
)
async def list_project_files(ctx: ToolContext, args: dict[str, Any]) -> Any:
    body = await call(ctx, "projects/get-project-files", {"record_id": args["project_id"], "module_key": "projects"})
    data = body.get("data") or {}
    files = []
    for row in (data.get("aws_files") if isinstance(data, dict) else None) or []:
        if not isinstance(row, dict):
            continue
        name, ext = text(row.get("file_name")) or "", text(row.get("file_ext")) or ""
        files.append(
            {
                "file_id": num(row.get("image_id")),
                "name": f"{name}.{ext}" if ext and not name.endswith(f".{ext}") else name or None,
                "title": text(row.get("title")),
                "is_image": bool(num(row.get("is_image"))),
                "size_bytes": num(row.get("size")),
                "url": text(row.get("file_path")),
                "thumbnail_url": text(row.get("thumb_file_path")),
                "notes": text(row.get("notes")),
                "tags": text(row.get("file_tags")),
                "added_on": text(row.get("date_added")),
            }
        )
    return {"files": files}
