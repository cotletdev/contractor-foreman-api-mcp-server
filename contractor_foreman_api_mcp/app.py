"""Everything the server knows about Contractor Foreman outside `contractor_foreman/`: names, domains, cookies.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "Contractor Foreman"
SLUG = "contractor-foreman"
# The command and the prefix of every environment variable (CONTRACTOR_FOREMAN_AUTH_TOKEN, ..._MCP_TOKEN ...).
CLI = "contractor-foreman-mcp"
ENV = "CONTRACTOR_FOREMAN"
# Requests may reach only these hosts and their subdomains. Their cookies are read from Chrome.
DOMAINS = ("contractorforeman.net",)
# Present together only while signed in (a signed-out visitor gets the first one too), with the domain a
# pasted token sets each on.
COOKIE_DOMAINS = {"_session__240322": "app.contractorforeman.net", "auth_data_session": ".contractorforeman.net"}
SESSION_COOKIES = tuple(COOKIE_DOMAINS)
LOGIN_URL = "https://app.contractorforeman.net/sign-in"
# A final URL with one of these means the app signed the session out.
LOGGED_OUT_MARKERS = ("/sign-in",)
# Paths a tool may never change: account, company setup, billing. Reads (GET) stay allowed; every other
# method to a match is refused before it leaves (core/context.py).
ACCOUNT_PATHS = (
    r"^/api/auth/",
    r"^/api/settings/",
    r"^/api/subscription",
    r"^/api/stripe",
    r"^/api/checkout-link",
    r"^/api/common/submit-cancellation-request",
    r"^/api/forgot-password",
    r"^/api/directory/\d+/dir-reset-password",
    r"^/api/remove-demo-data",
    r"^/api/common/replicate-demo-data",
)
# A 401 or 403 whose body has one of these asks to sign in again: auth_expired. Contractor Foreman has none.
RELOGIN_MARKERS: tuple[str, ...] = ()
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/contractor-foreman"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = "Start with list_projects: its `project_id` values are what most other tools take."
