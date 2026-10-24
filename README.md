# Contractor Foreman API and MCP server, self-hosted

A **Contractor Foreman API** and a **Contractor Foreman MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. All 89 Contractor Foreman tools we run in production at [Cotlet](https://cotlet.dev/integrations/contractor-foreman-api-mcp-server): projects, schedule, daily logs, punchlists, to-dos, estimates, change orders, invoices, payments, job costing, directory, leads, time cards, bills, purchase orders, sub-contracts, work orders, service tickets, RFIs, submittals and inspections.

Contractor Foreman has no public API and no official MCP server. This repo gives you both:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/contractor-foreman`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("list_projects", search="Oak St")`, plus 10 ready scripts in [`examples/`](examples/).

It is for technical people who want to run it themselves, **for noncommercial use only** ([license](#license)). If you want it running 24/7 on a server, kept working when Contractor Foreman changes its app, for a team or a business, use the [hosted version at cotlet.dev](https://cotlet.dev/integrations/contractor-foreman-api-mcp-server).

[![Contractor Foreman MCP server](https://img.shields.io/badge/Contractor%20Foreman%20MCP-89%20tools-6d4aef)](#all-89-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-141318)](LICENSE)
[![MCP Badge](https://lobehub.com/badge/mcp/cotletdev-contractor-foreman-api-mcp-server)](https://lobehub.com/mcp/cotletdev-contractor-foreman-api-mcp-server)

```bash
git clone https://github.com/cotletdev/contractor-foreman-api-mcp-server.git && cd contractor-foreman-api-mcp-server
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
contractor-foreman-mcp connect                     # reads your Contractor Foreman session from Chrome
contractor-foreman-mcp call list_projects
claude mcp add contractor-foreman -- "$PWD/.venv/bin/contractor-foreman-mcp" mcp
```

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 89 tools](#all-89-tools)
- [Configuration](#configuration)
- [Security and your Contractor Foreman account](#security-and-your-contractor-foreman-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ contractor-foreman-mcp on your computer ──your cookies──▶ app.contractorforeman.net
                                                      ▲
                     contractor-foreman-mcp connect ──┘ reads them once from your Chrome (DevTools Protocol)
```

1. You sign in to Contractor Foreman in your own Chrome, the way you always do.
2. `contractor-foreman-mcp connect` attaches to that Chrome through the Chrome DevTools Protocol, reads the contractorforeman.net cookies and your browser's time zone, and saves them to `~/.config/contractor-foreman-api-mcp/session.json`, readable by your user only. It never sees or stores your password.
3. Every tool call is a request to the same `/api/...` endpoints the Contractor Foreman web app calls, with those cookies, sent with [curl_cffi](https://github.com/lexiforest/curl_cffi), which copies Chrome's TLS fingerprint. No browser runs for a call.

Contractor Foreman answers a signed-out request with HTTP 200 and a "signed out" body, and the tools turn that into `auth_expired`. The server then reads the cookies from Chrome again, if Chrome is open with remote debugging on. Times you send are saved in the time zone `connect` read from Chrome.

## Requirements

- Python 3.11 or newer.
- Google Chrome 144 or newer, signed in to Contractor Foreman. Any Chrome or Chromium works with a [debugging port](#option-b-a-chrome-with-a-debugging-port).
- macOS, Linux or Windows.
- A Contractor Foreman role with access to the modules you use. A tool on a module your role cannot open fails with the app's own message.

## Install

```bash
git clone https://github.com/cotletdev/contractor-foreman-api-mcp-server.git
cd contractor-foreman-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
contractor-foreman-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run contractor-foreman-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `git pull && pip install -e .`. We copy every change of the hosted Contractor Foreman tools into this repo.

## Connect your Chrome

### Option A: your everyday Chrome (recommended)

1. Open `chrome://inspect/#remote-debugging` in Chrome and switch **remote debugging** on. Chrome then accepts DevTools connections from programs on this computer, and asks you before each one.
2. Make sure you are signed in at [app.contractorforeman.net](https://app.contractorforeman.net).
3. Run:

   ```bash
   contractor-foreman-mcp connect
   ```

4. Chrome asks whether to allow the connection. Click **Allow**.

```text
Saved 34 Contractor Foreman cookies to /Users/you/.config/contractor-foreman-api-mcp/session.json
Signed in to Contractor Foreman as Mike Turner (mike@turnerbuilds.com)
```

You can switch remote debugging off again afterwards. Leave it on if you want the server to pick up a new session by itself after Contractor Foreman signs you out.

`connect` looks for Chrome's `DevToolsActivePort` file in the default profile folder. For Chrome Beta, Canary or a custom profile folder, pass `--profile-dir "<folder>"`.

### Option B: a Chrome with a debugging port

Chrome does not open a debugging port on your default profile, so start a separate one, sign in to Contractor Foreman there once, and connect to it:

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-contractor-foreman"
# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-contractor-foreman"
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-contractor-foreman"

contractor-foreman-mcp connect --cdp http://127.0.0.1:9222
```

`--cdp` also takes a `ws://` DevTools URL, for example of a Chrome on another machine reached over an SSH tunnel.

### Option C: paste the cookies by hand

For a server with no Chrome: in Chrome open DevTools on app.contractorforeman.net, **Application > Cookies**, and copy two values: `_session__240322` (under https://app.contractorforeman.net) and `auth_data_session` (under .contractorforeman.net). Then:

```bash
contractor-foreman-mcp connect --token     # paste "_session__240322=...; auth_data_session=...", input is hidden
# or, without a session file:
export CONTRACTOR_FOREMAN_AUTH_TOKEN='_session__240322=...; auth_data_session=...'
```

Pasted cookies are not refreshed on their own. Paste new ones when Contractor Foreman signs you out. Without Chrome the time zone is this machine's (`TZ` or the system setting).

Check the session at any time:

```bash
contractor-foreman-mcp status
```

## MCP server

The MCP server lists every tool with its input schema, a description written for agents, and hints: read tools are marked read-only, and tools that email documents to clients are marked so your client asks before running them.

### Claude Code

```bash
claude mcp add contractor-foreman -- /path/to/contractor-foreman-api-mcp-server/.venv/bin/contractor-foreman-mcp mcp
# read only:
claude mcp add contractor-foreman -- /path/to/contractor-foreman-api-mcp-server/.venv/bin/contractor-foreman-mcp mcp --read-only
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "contractor-foreman": {
      "command": "/path/to/contractor-foreman-api-mcp-server/.venv/bin/contractor-foreman-mcp",
      "args": ["mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.contractor-foreman]
command = "/path/to/contractor-foreman-api-mcp-server/.venv/bin/contractor-foreman-mcp"
args = ["mcp"]
```

### Over HTTP

`contractor-foreman-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
contractor-foreman-mcp serve
claude mcp add --transport http contractor-foreman http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *Here is Mike's voice note from the Maple St remodel. Turn it into today's daily log: framing crew of 4, one electrician, drywall delivered, rain stopped work at 2:30.*
>
> *Turn this scope list from the Johnson bathroom walkthrough into an estimate with 20% markup on materials, show me the total, then email it to the client.*
>
> *Which open projects have cost codes running over the estimate? Show the biggest overruns first.*
>
> *List overdue invoices with the balance and days late, then record the $1,200 check from Burger Palace against invoice 11.*

## REST API

```bash
contractor-foreman-mcp serve       # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/contractor-foreman`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments, and a JSON body adds the rest.

```bash
curl 'http://127.0.0.1:8787/api/v1/contractor-foreman/projects?search=Oak%20St'
curl 'http://127.0.0.1:8787/api/v1/contractor-foreman/projects/1678164/job-costing'
curl 'http://127.0.0.1:8787/api/v1/contractor-foreman/invoices?unpaid_only=true'
curl -X POST http://127.0.0.1:8787/api/v1/contractor-foreman/daily-logs \
  -H 'Content-Type: application/json' \
  -d '{"project_id": "1678164", "date": "2026-10-20", "notes": "Hung and taped drywall in the dining area.", "people": {"Drywall crew": 3}}'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/contractor-foreman/tools/list_todos -d '{"status": "open"}'
```

- `GET /api/v1/contractor-foreman/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.
- Answers are JSON. Lists return `next_cursor`; pass it back as `cursor` for the next page.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
CONTRACTOR_FOREMAN_MCP_TOKEN=$(openssl rand -hex 24) contractor-foreman-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from contractor_foreman_api_mcp import call
from contractor_foreman_api_mcp.scripting import paginate, write_rows

projects = list(paginate("list_projects", {"include_completed": True, "limit": 100}, "projects"))
write_rows(projects, "projects.csv")
costing = call("get_job_costing", project_id=projects[0]["project_id"])
call("create_daily_log", project_id=projects[0]["project_id"], date="2026-10-20", notes="Framed the east wall.")
```

Or one tool from the shell: `contractor-foreman-mcp call list_invoices unpaid_only=true limit=10`, or with a JSON object.

Ready scripts in [`examples/`](examples/). Each prints JSON or a short report, takes `--out file.csv` or `--out file.json` where it makes sense, and `--help`:

| Script | What it does |
|---|---|
| [`export_projects.py`](examples/export_projects.py) | Projects to CSV or JSON: customer, stage, dates, contract amount, costs, percent complete. `--status`, `--search`. |
| [`add_daily_log.py`](examples/add_daily_log.py) | A daily log from a site note, crews and deliveries, after checking the day has no log yet. `--dry-run`. |
| [`create_estimate.py`](examples/create_estimate.py) | An estimate from a scope list in CSV with markup. Prints the total, `--send` emails the PDF. |
| [`create_change_order.py`](examples/create_change_order.py) | A change order or change order request from a client request; `--send` emails a saved one. |
| [`reschedule_task.py`](examples/reschedule_task.py) | Moves a schedule task by N days and every task that depends on it. `--dry-run`. |
| [`over_budget_projects.py`](examples/over_budget_projects.py) | Cost codes of open projects whose actual cost runs past the estimate, biggest overrun first. |
| [`overdue_invoices.py`](examples/overdue_invoices.py) | Past-due invoices with a balance, oldest first, with days overdue and the total outstanding. |
| [`record_payment.py`](examples/record_payment.py) | Records a check or transfer against an invoice found by its number, prints the new balance. |
| [`crew_hours.py`](examples/crew_hours.py) | Hours and labor cost per project and employee from time cards, for the last N days or a date range. |
| [`open_todos.py`](examples/open_todos.py) | Open to-dos due in the next N days or already late, by project. |

```bash
python examples/overdue_invoices.py --out overdue.csv
python examples/add_daily_log.py --project-id 1678164 --notes "Framed second floor east wall." --people "Framing crew=4" --dry-run
```

On a schedule, cron on your own computer works while it is on: `0 8 * * 1 cd ~/contractor-foreman-api-mcp-server && .venv/bin/python examples/overdue_invoices.py --out overdue.csv`.

## All 89 tools

Ids come from the list tools: `project_id` from `list_projects`, `invoice_id` from `list_invoices` and so on. `contractor-foreman-mcp tools` prints this list, `contractor-foreman-mcp tools --json` adds the input schemas. Every tool of the hosted version is in this repo.

### Projects, schedule, daily logs, punchlists and to-dos (18)

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `create_daily_log` | write | `POST /daily-logs` | New daily log on a project: work notes, people, deliveries, weather notes and delays. |
| `create_project` | write | `POST /projects` | New project for a customer, with number, type, stage, address and dates. |
| `create_punchlist` | write | `POST /punchlists` | New, empty punchlist on a project. |
| `create_todo` | write | `POST /todos` | New to-do, optionally on a project, with due date, priority and assignees. |
| `get_daily_log` | read | `GET /daily-logs/{daily_log_id}` | One daily log: work notes, people and visitors, materials, equipment, weather and delays. |
| `get_job_costing` | read | `GET /projects/{project_id}/job-costing` | Estimated and actual cost per cost code for one project, with the difference and totals. |
| `get_project` | read | `GET /projects/{project_id}` | One project: customer, address, stage, dates, contract amounts, costs, billing and retainage. |
| `get_punchlist` | read | `GET /punchlists/{punchlist_id}` | One punchlist: project, address, customer and how many items are open and completed. |
| `get_todo` | read | `GET /todos/{todo_id}` | One to-do: description, project, priority, status, due date, assignees and checklist. |
| `list_daily_logs` | read | `GET /daily-logs` | Daily logs by date, optionally for one project and a date range. |
| `list_projects` | read | `GET /projects` | Projects with customer, stage, dates, contract amount, costs and percent complete. |
| `list_punchlists` | read | `GET /punchlists` | Punchlists with project, status, open and completed item counts and who the items are assigned to. |
| `list_schedule_tasks` | read | `GET /projects/{project_id}/schedule-tasks` | Gantt schedule tasks of a project: dates, duration, dependencies, assignees, percent complete. |
| `list_todos` | read | `GET /todos` | To-dos with project, priority, status, due date and assignees. |
| `update_daily_log` | write | `PATCH /daily-logs/{daily_log_id}` | Change the notes, times, people, deliveries, weather notes or delays of a daily log. |
| `update_project` | write | `PATCH /projects/{project_id}` | Change a project's name, stage, type, address, dates or description. |
| `update_schedule_task` | write | `PATCH /projects/{project_id}/schedule-tasks/{task_id}` | Change the name, dates, length or percent complete of a task on the project schedule. |
| `update_todo` | write | `PATCH /todos/{todo_id}` | Change a to-do's name, description, due date, priority or status, e.g. mark it complete. |

### Estimates, change orders, invoices and payments (27)

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `add_change_order_items` | write | `POST /change-orders/{change_order_id}/items` | Adds priced line items to a change order or change order request. |
| `add_estimate_items` | write | `POST /estimates/{estimate_id}/items` | Adds priced line items to an existing estimate. |
| `add_invoice_items` | write | `POST /invoices/{invoice_id}/items` | Adds priced line items to an invoice. |
| `create_change_order` | write | `POST /change-orders` | Creates a change order or change order request on a project, with line items. |
| `create_estimate` | write | `POST /estimates` | Creates a draft estimate on a project or for a customer, with priced line items. |
| `create_invoice` | write | `POST /invoices` | Creates a draft invoice for a project or customer, with priced line items. |
| `create_share_link` | write | `POST /share-links` | Makes a short internal link that opens an estimate, change order or invoice for your signed-in team. |
| `delete_change_order` | write | `DELETE /change-orders/{change_order_id}` | Deletes a change order or change order request for good. |
| `delete_estimate` | write | `DELETE /estimates/{estimate_id}` | Deletes an estimate for good. |
| `delete_invoice` | write | `DELETE /invoices/{invoice_id}` | Deletes an invoice that has no payments, for good. |
| `get_change_order` | read | `GET /change-orders/{change_order_id}` | One change order or request with description, status, total and line items. |
| `get_estimate` | read | `GET /estimates/{estimate_id}` | One estimate with customer, dates, terms, totals and every line item. |
| `get_invoice` | read | `GET /invoices/{invoice_id}` | One invoice with customer, dates, terms, line items, payments and balance due. |
| `list_change_orders` | read | `GET /change-orders` | Change orders and change order requests, newest first, with status, project and total. |
| `list_cost_codes` | read | `GET /cost-codes` | The company's cost codes, to put on estimate, change order and invoice items. |
| `list_cost_items` | read | `GET /cost-items` | Saved cost items with unit, unit cost and markup, to price estimate and change order lines. |
| `list_estimates` | read | `GET /estimates` | Estimates, newest first, with status, project, customer and total. |
| `list_invoices` | read | `GET /invoices` | Invoices, newest first, with status, totals, balance due and an overdue flag. |
| `list_payments` | read | `GET /payments` | Payments received on invoices, newest first, with amount, method and invoice. |
| `record_payment` | write | `POST /invoices/{invoice_id}/payments` | Records a payment you received against an invoice. |
| `remove_estimate_items` | write | `DELETE /estimates/{estimate_id}/items` | Deletes line items from an estimate. |
| `send_change_order` | write | `POST /change-orders/{change_order_id}/send` | Emails the change order as a PDF to the customer or to the addresses you give. |
| `send_estimate` | write | `POST /estimates/{estimate_id}/send` | Emails the estimate as a PDF to the customer or to the addresses you give. |
| `send_invoice` | write | `POST /invoices/{invoice_id}/send` | Emails the invoice as a PDF to the customer or to the addresses you give. |
| `update_change_order` | write | `PATCH /change-orders/{change_order_id}` | Changes a change order's status, title, reason or date. |
| `update_estimate` | write | `PATCH /estimates/{estimate_id}` | Changes an estimate's status, title, dates, description, inclusions or exclusions. |
| `update_invoice` | write | `PATCH /invoices/{invoice_id}` | Changes an invoice's status, invoice date, due date or description. |

### Directory, leads, time cards, purchasing and field work (44)

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `add_project_note` | write | `POST /projects/{project_id}/notes` | Adds a note to a project's Notes tab. |
| `create_bill` | write | `POST /bills` | Records a vendor bill with its line items, optionally against a project. |
| `create_contact` | write | `POST /contacts` | Adds a customer, employee, contractor, vendor or misc contact to the Directory. |
| `create_expense` | write | `POST /expenses` | Records an expense (receipt, purchase, fee) with amount, date, vendor and project. |
| `create_inspection` | write | `POST /inspections` | Logs an inspection on a project with type, date, agency, inspector and notes. |
| `create_lead` | write | `POST /leads` | Adds a sales lead with contact details and a pipeline stage. |
| `create_opportunity` | write | `POST /opportunities` | Adds a sales opportunity for a customer with stage, score, budget and expected sale date. |
| `create_purchase_order` | write | `POST /purchase-orders` | Creates a draft purchase order to a supplier with line items, optionally for a project. |
| `create_rfi` | write | `POST /rfis` | Drafts a request for information on a project, with the question and a reply-by date. |
| `create_service_ticket` | write | `POST /service-tickets` | Opens a service ticket for a customer, optionally scheduled for a date and time. |
| `create_sub_contract` | write | `POST /sub-contracts` | Creates a draft sub-contract with a subcontractor on a project. |
| `create_work_order` | write | `POST /work-orders` | Creates an Open work order on a project with subject, description and dates. |
| `get_bill` | read | `GET /bills/{bill_id}` | One vendor bill with its line items, dates, total, balance due and status. |
| `get_clock_status` | read | `GET /clock-status` | Who is clocked in right now, whether you are, and this and last week's crew hours. |
| `get_contact` | read | `GET /contacts/{contact_id}` | One Directory record in full: contact details, status, services, terms and additional contacts. |
| `get_expense` | read | `GET /expenses/{expense_id}` | One expense with amount, date, vendor, project, cost type, cost code and reason. |
| `get_inspection` | read | `GET /inspections/{inspection_id}` | One inspection with type, project, date, result, agency, inspector and notes. |
| `get_opportunity` | read | `GET /opportunities/{opportunity_id}` | One opportunity in full: customer contact, stage, score, budget, notes and last activity. |
| `get_purchase_order` | read | `GET /purchase-orders/{purchase_order_id}` | One purchase order with supplier, dates, status and its line items. |
| `get_rfi` | read | `GET /rfis/{rfi_id}` | One RFI with its question, dates, answer and status. |
| `get_service_ticket` | read | `GET /service-tickets/{service_ticket_id}` | One service ticket with customer, service address, schedule, technicians and priority. |
| `get_sub_contract` | read | `GET /sub-contracts/{sub_contract_id}` | One sub-contract with subcontractor, amounts, retainage, scope of work and items. |
| `get_submittal` | read | `GET /submittals/{submittal_id}` | One submittal with plan sheet, specification section, status, dates and its items. |
| `get_time_card` | read | `GET /time-cards/{timecard_id}` | One time card or crew sheet with hours per employee and cost code. |
| `get_work_order` | read | `GET /work-orders/{work_order_id}` | One work order with project, customer, status, dates, location, notes and items. |
| `list_bills` | read | `GET /bills` | Vendor bills with vendor, project, dates, total, balance due and status. |
| `list_contacts` | read | `GET /contacts` | Customers, employees, contractors, vendors and misc contacts from the Directory. |
| `list_expenses` | read | `GET /expenses` | Expenses with amount, date, vendor, project, cost type and who paid. |
| `list_inspections` | read | `GET /inspections` | Inspections with project, type, date, result, agency and permit number. |
| `list_leads` | read | `GET /leads` | Sales leads with contact details, stage and quality score. |
| `list_opportunities` | read | `GET /opportunities` | Sales opportunities with customer, stage, score, budget and expected sale date. |
| `list_project_crew_hours` | read | `GET /projects/{project_id}/crew-hours` | Hours and labor cost logged on one project, per employee and per day and cost code. |
| `list_project_files` | read | `GET /projects/{project_id}/files` | Photos and documents on a project, with name, size and a download link. |
| `list_project_notes` | read | `GET /projects/{project_id}/notes` | The notes on a project's Notes tab, with author and time. |
| `list_purchase_orders` | read | `GET /purchase-orders` | Purchase orders with supplier, project, order date, total and status. |
| `list_rfis` | read | `GET /rfis` | Requests for information with question, project, dates, answer and status. |
| `list_service_tickets` | read | `GET /service-tickets` | Service tickets with customer, status, service date and time and technicians. |
| `list_sub_contracts` | read | `GET /sub-contracts` | Sub-contracts with subcontractor, project, amount, billed, paid, balance and status. |
| `list_submittals` | read | `GET /submittals` | Submittals with project, status, date received, due date and approver. |
| `list_time_cards` | read | `GET /time-cards` | Time cards with employee or crew, project, clock-in and clock-out times and hours, newest first. |
| `list_work_orders` | read | `GET /work-orders` | Work orders with project, customer, status, dates, total and assignee. |
| `record_inspection_result` | write | `PUT /inspections/{inspection_id}/result` | Marks an inspection passed, failed or to re-inspect, optionally with notes. |
| `update_service_ticket_status` | write | `PUT /service-tickets/{service_ticket_id}/status` | Moves a service ticket to scheduled, en route, checked in, completed, closed and so on. |
| `update_work_order_status` | write | `PUT /work-orders/{work_order_id}/status` | Moves a work order to open, estimating, submitted, approved, canceled or completed. |

Never built, on purpose: your Contractor Foreman sign-in, password, email and two-factor settings, company settings, the subscription and billing, and the demo data switch. Every request passes a guard that refuses those Contractor Foreman paths.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `CONTRACTOR_FOREMAN_MCP_HOME` | `~/.config/contractor-foreman-api-mcp` | Folder of `session.json`. |
| `CONTRACTOR_FOREMAN_AUTH_TOKEN` | | The session cookies as `_session__240322=...; auth_data_session=...`, instead of `contractor-foreman-mcp connect`. |
| `CONTRACTOR_FOREMAN_PROXY` | | Proxy for every request to Contractor Foreman, e.g. `http://user:pass@host:port`. |
| `CONTRACTOR_FOREMAN_MCP_READ_ONLY` | | `1` hides and refuses every tool that changes Contractor Foreman (same as `--read-only`). |
| `CONTRACTOR_FOREMAN_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `CONTRACTOR_FOREMAN_MCP_HOST`, `CONTRACTOR_FOREMAN_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |

## Security and your Contractor Foreman account

- **Your password never reaches this code.** Only cookies are read, and only those of contractorforeman.net.
- **The session file is yours.** `session.json` is created with mode 0600. Anyone who has it can act as you in Contractor Foreman, so keep it out of git and shared folders.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `CONTRACTOR_FOREMAN_MCP_TOKEN`.
- **contractorforeman.net only.** Requests and redirects to other hosts are refused.
- **Read-only mode.** `--read-only` or `CONTRACTOR_FOREMAN_MCP_READ_ONLY=1` exposes the 48 read tools only.
- **Some actions reach clients.** `send_estimate`, `send_change_order` and `send_invoice` email a PDF from your account, and a new to-do shows up in its assignees' app. MCP clients ask before running them. A script does not, so try it on a test project first.
- **Deletes are final.** `delete_estimate`, `delete_change_order` and `delete_invoice` remove the record as the app's own delete does.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required`, `auth_expired` | No session, or Contractor Foreman signed you out. Sign in in Chrome and run `contractor-foreman-mcp connect`. |
| 403 | `app_permission_denied` | Your Contractor Foreman role cannot open that module. |
| 403 | `scope_denied` | The server runs read-only, or the request would change account settings or billing. |
| 403 | `target_blocked` | Contractor Foreman refused the request or showed a bot check. Open the app in Chrome once, then retry. |
| 409 | `captcha_required` | Contractor Foreman asks for a CAPTCHA. Solve it in Chrome. |
| 422 | `invalid_input` | An argument is missing or wrong; the message names it. |
| 429 | `rate_limited` | Contractor Foreman is limiting the account. Wait a few minutes. |
| 502 | `target_error` | Contractor Foreman answered with an error (the message quotes it), or changed its app. `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/contractor-foreman-api-mcp-server/issues). |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/contractor-foreman-api-mcp-server) |
|---|---|---|
| Tools | the same 89 | the same 89 |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Contractor Foreman session | your Chrome, cookies in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM |
| When Contractor Foreman changes its app | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Approvals | your MCP client asks per call | emails to clients wait for your OK, switchable per tool |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, Zapier, any HTTP client |
| Who may use it | you, for noncommercial use | teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 20 to 30 credits (25 for most tools), failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Does Contractor Foreman have an official API?**
No public one: no REST API, developer docs or API keys (checked 11 Oct 2026). The only programmatic access is a Zapier app with 7 triggers for leads, customers and file uploads, and 2 actions, Create Lead and Create Customer. It cannot read or write estimates, change orders, daily logs, the schedule, invoices or job costing. Details: [cotlet.dev/integrations/contractor-foreman-api-mcp-server](https://cotlet.dev/integrations/contractor-foreman-api-mcp-server).

**Is there a Contractor Foreman MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `contractor-foreman-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted Contractor Foreman MCP server](https://cotlet.dev/integrations/contractor-foreman-api-mcp-server) gives you.

**Is this a scraper?**
It does what people want a scraper for (export projects, invoices and time cards to CSV) but parses no HTML. It calls the same JSON endpoints the Contractor Foreman web app calls, in your own account.

**Can I export projects, invoices or crew hours to CSV?**
Yes: `python examples/export_projects.py --out projects.csv`, `python examples/overdue_invoices.py --out overdue.csv` or `python examples/crew_hours.py --days 30 --out hours.csv`. Pages are followed automatically.

**Can an agent write my daily logs?**
Yes. `create_daily_log` takes the notes, crews with headcounts, deliveries and weather remarks. Contractor Foreman records the weather for the date and address itself. `examples/add_daily_log.py` first checks that the day has no log yet.

**Why does it need my Chrome?**
To read your Contractor Foreman session without your password. Chrome is used once per sign-in, not for each call.

**What happens when Contractor Foreman signs me out?**
Calls fail with `auth_expired`. With Chrome remote debugging on, the server reads the new cookies on the next call (click Allow when Chrome asks). Otherwise run `contractor-foreman-mcp connect` again.

**Can it run on a VPS or in Docker?**
Technically yes, with `CONTRACTOR_FOREMAN_AUTH_TOKEN`. Contractor Foreman then sees your session from a datacenter IP, which looks less like you. For an always-on setup the hosted version keeps your session in your own Cloud Browser on a fixed IP.

**Can I use it at work or for my clients?**
No, the license allows noncommercial use only, and running your own contracting business on it is business use. For a team, a company or client work, use [Cotlet](https://cotlet.dev) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Is it open source?**
The source is public, the license is not an open source license: noncommercial use only, no business use.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/contractor-foreman-api-mcp-server/issues) with the tool name and the error message.

## License

[PolyForm Noncommercial License 1.0.0](LICENSE). In short:

- **Allowed:** noncommercial use: you, for your own personal purposes with your own Contractor Foreman account, or a charity, school, public research or government body. Changing the code, and sharing it under the same license.
- **Not allowed:** any commercial use, your own business included; client work; selling or offering it, or a service built on it.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev) ([@cotletdev](https://x.com/cotletdev)). Contractor Foreman is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by Contractor Foreman.
