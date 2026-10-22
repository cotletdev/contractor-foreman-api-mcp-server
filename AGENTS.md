# AGENTS.md

You are an AI agent in a clone of this repo. It is a self-hosted Contractor Foreman API and MCP server: 89 tools that work in the user's own Contractor Foreman account, through the session of their own Google Chrome. Your usual job is one of three: set it up for the user, use its tools for them, or change its code. Human docs: `README.md`.

## Before you start

- The license allows personal use by one person only (`LICENSE`). If the user is setting this up for a company, a team or clients, say so and point to the hosted version at https://cotlet.dev/integrations/contractor-foreman-api-mcp-server. Do not continue the setup for that use.
- Every tool acts as the user in Contractor Foreman. Tools with access `write` create, change or delete records the user's office and crews see, and `send_estimate`, `send_change_order` and `send_invoice` email a PDF to the client.

## Set it up for the user

Do the steps yourself. Ask the user only for what needs their hands in Chrome.

1. Check Python: `python3 --version` must be 3.11 or newer.
2. Install in the repo root:

   ```bash
   python3 -m venv .venv && .venv/bin/pip install -e .
   .venv/bin/contractor-foreman-mcp --version
   ```

   On Windows the path is `.venv\Scripts\contractor-foreman-mcp`. With uv: `uv venv && uv pip install -e .`.
3. Ask the user to do two things in Chrome. You cannot open `chrome://` pages for them.
   - Open `chrome://inspect/#remote-debugging` and switch remote debugging on.
   - Be signed in at https://app.contractorforeman.net.
4. Run `.venv/bin/contractor-foreman-mcp connect`. Tell the user to click **Allow** when Chrome asks about the connection. Success prints `Signed in to Contractor Foreman as <name> (<email>)`.
5. Check: `.venv/bin/contractor-foreman-mcp status`, then `.venv/bin/contractor-foreman-mcp call list_projects limit=5`.
6. Add the MCP server to the user's client. Use the absolute path of `.venv/bin/contractor-foreman-mcp`:
   - Claude Code: `claude mcp add contractor-foreman -- <abs path>/.venv/bin/contractor-foreman-mcp mcp`
   - Claude Desktop, Cursor, Codex: the config blocks in `README.md`, section "MCP server".
   - Add `--read-only` after `mcp` if the user only wants to read.
   The client loads new MCP servers on its next start. Tell the user.

If step 4 fails:

| Message | What to do |
|---|---|
| `Chrome remote debugging is off` | Step 3 is not done, or Chrome is Beta, Canary or a custom profile: pass `--profile-dir "<profile folder>"`. |
| `Could not connect to Chrome` | The user did not click Allow, or Chrome is closed. Run `connect` again. |
| `This Chrome is not signed in to Contractor Foreman` | The user signs in at app.contractorforeman.net in that Chrome, then run `connect` again. |
| No Chrome on this machine (a server) | The user copies the `_session__240322` and `auth_data_session` cookies from Chrome DevTools (Application, Cookies) and runs `contractor-foreman-mcp connect --token` themselves, pasting `_session__240322=...; auth_data_session=...`. Never ask them to paste the cookies into the chat. |

## Use the tools

- With the MCP server added, call its tools. Without it: `.venv/bin/contractor-foreman-mcp call <tool> key=value ...`, or one JSON object as the argument.
- `.venv/bin/contractor-foreman-mcp tools` lists every tool with access and route. `tools --json` adds the input schemas.
- Start with `list_projects`. Its `project_id` values are what most tools take. Other ids come from the matching list tool (`list_invoices`, `list_estimates`, `list_contacts` ...).
- Lists return `next_cursor`. Pass it back as `cursor` for the next page.
- Before a `write` tool, show the user what you will save or send and to whom, and get their OK. Deletes cannot be undone.
- For a script or a cron job, use `contractor_foreman_api_mcp.scripting` (`call`, `paginate`, `write_rows`) and the scripts in `examples/` as models.
- For a REST API (n8n, other languages): `.venv/bin/contractor-foreman-mcp serve`, routes under `http://127.0.0.1:8787/api/v1/contractor-foreman`, docs at `/docs`.

Errors come as `<code>: <message>`. `auth_expired` means Contractor Foreman signed the session out: the user signs in again in Chrome and you run `connect`. `target_error` quotes Contractor Foreman's own message, which usually names the missing field or the module the role cannot open. More codes: `README.md`, section "Errors".

## Keep secrets out

- `~/.config/contractor-foreman-api-mcp/session.json` and `CONTRACTOR_FOREMAN_AUTH_TOKEN` give full access to the user's Contractor Foreman account. Never print, log, commit or copy their content.
- `serve` listens on 127.0.0.1. Never start it on another address without `CONTRACTOR_FOREMAN_MCP_TOKEN`.

## Change the code

| Path | What | Edit? |
|---|---|---|
| `contractor_foreman_api_mcp/contractor_foreman/` | the Contractor Foreman tools, one file per tool in `tools/`, shared helpers in `tools/_*.py`, the request code in `client.py` | Yes for a local fix, but the next `git pull` brings our version of these files. Report the bug at https://github.com/cotletdev/contractor-foreman-api-mcp-server/issues |
| `contractor_foreman_api_mcp/app.py` | app name, domains, session cookies, account paths, REST prefix | Rarely |
| `contractor_foreman_api_mcp/core/` | `@tool` declaration, errors, the account guard, the HTTP client with the session (`context.py`) | Yes |
| `contractor_foreman_api_mcp/session.py` | reading cookies and the time zone from Chrome over CDP, the session file | Yes |
| `contractor_foreman_api_mcp/runner.py`, `api.py`, `mcp_server.py`, `cli.py` | tool registry, REST API, MCP server, command line | Yes |
| `examples/` | scripts for common jobs | Yes |

A new tool is a new file in `contractor_foreman_api_mcp/contractor_foreman/tools/` with a `@tool(...)` declaration (name, access, input schema, `route`). The registry finds it, and the REST API, the MCP server and the CLI show it without other changes.

There is no test suite. After a change, run `.venv/bin/contractor-foreman-mcp tools` and one read tool against the user's account.
