"""

My Financial Tracker — a very basic MCP server for managing personal finances

Features demonstrated:
  ┌─ SECTION A: Core utility tools ────────────────────────────────────┐
  │  calculate                    — safe AST arithmetic evaluator      │
  │  get_file_path                — resolve invoices/receipts path     │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ SECTION B: Receipt management ────────────────────────────────────┐
  │  prepare_receipt             — Google Vision OCR + LLM extraction  │
  │  commit_receipt              — persist prepared receipts           │
  │  filter_receipts             — fetch existing receipts             │
  │  update_receipt              — update receipt metadata             │
  │  add_receipt_item            — append receipt line items           │
  │                                                                    │
  │  Integrations:                                                     │
  │   • Google Vision OCR                                              │
  │   • Google Drive archival                                          │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ SECTION C: Transactions & categorization ─────────────────────────┐
  │  prepare_transation          — draft financial transactions        │
  │  commit_transaction          — persist confirmed transactions      │
  │  update_transaction          — update receipt-linked items         │
  │  get_transactions            — query transactions by filters       │
  │                                                                    │
  │  Features:                                                         │
  │   • semantic category recognition                                  │
  │   • manual and receipt-linked payments                             │
  │   • automatic empty-receipt association for standalone operations  │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ SECTION D: Invoice management ────────────────────────────────────┐
  │  prepare_invoice             — Google Vision OCR + LLM extraction  │
  │  commit_invoice              — persist prepared invoices           │
  │  update_invoice              — update invoice status/payment       │
  │  filter_invoices             — query invoices by status/date       │
  │                                                                    │
  │  Features:                                                         │
  │   • supplier/customer invoices                                     │
  │   • credits/debts tracking                                         │
  │   • Google Calendar integration                                    │
  │   • Google Drive archival                                          │
  │   • automatic payment reminders                                    │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ SECTION E: Financial events & reminders ──────────────────────────┐
  │  add_future_purchase_to_calendar — schedule future payments        │
  │  get_events                      — fetch reminders and due events  │
  │                                                                    │
  │  REST endpoints:                                                   │
  │   /api/payments/confirm/purchase                                   │
  │   /api/payments/confirm/customer_invoice                           │
  │   /api/payments/confirm/supplier_invoice                           │
  │                                                                    │
  │  Integrations:                                                     │
  │   • Google Calendar                                                │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ SECTION F: MCP prompts & AI workflows ────────────────────────────┐
  │  transactions_assistant     — Italian financial workflow assistant │
  │  build_category_prompt      — semantic transaction categorization  │
  │                                                                    │
  │  AI workflow model:                                                │
  │   prepare → user confirmation → commit                             │
  │                                                                    │
  │  Validation rules:                                                 │
  │   • never commit without confirmation                              │
  │   • semantic category normalization                                │
  │   • OCR structured extraction                                      │
  │   • concise multilingual-safe outputs                              │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ SECTION G: Authentication & OAuth ────────────────────────────────┐
  │  MCP spec OAuth 2.0 support                                        │
  │  ConsentOAuthProvider + PersistentOAuthProvider                    │
  │  Dynamic client registration (/register)                           │
  │  Token persistence with refresh/access token storage               │
  │  Google OAuth callback integration                                 │
  │  Stateful MCP notifications via SSE elicitation                    │
  │                                                                    │
  │  Custom routes:                                                    │
  │   /auth                                                            │
  │   /oauth/callback                                                  │
  │   /oauth/consent                                                   │
  │   /health                                                          │
  │   /auth-status                                                     │
  └────────────────────────────────────────────────────────────────────┘

  ┌─ Cross-cutting concerns ───────────────────────────────────────────┐
  │  FastMCP 3.x stateful StreamableHTTP transport                     │
  │  Lifespan-based shared dependency initialization                   │
  │  SQLite relational persistence layer                               │
  │  Google Drive integration                                          │
  │  Google Calendar integration                                       │
  │  Google Vision OCR integration                                     │
  │  OCR + LLM structured document extraction                          │
  │  Semantic AI categorization engine                                 │
  │  Stateful prepare/confirm/commit financial workflows               │
  │  Automatic payment reminder orchestration                          │
  │  MCP-compatible OAuth consent flow                                 │
  │  CORS support for browser-based MCP clients                        │
  │  Registration compatibility middleware for MCP SDK clients         │
  └────────────────────────────────────────────────────────────────────┘

  * Note: currently this system can't be used in production because it requests a lot of improvements and extensions
"""
from __future__ import annotations

import ast
import json
import logging
import operator
import os
from string import Template
from contextlib import asynccontextmanager
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any
import json
from datetime import datetime
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path
from fastapi import FastAPI

from my_financial_tracker_mcp.services.google_drive import DriveService
from my_financial_tracker_mcp.services.google_calendar import CalendarService
from my_financial_tracker_mcp.services.financial_events import FinancialEventsService
from my_financial_tracker_mcp.web_services.payments import Payments

from my_financial_tracker_mcp.tools.financial_events import FinancialEvents
from my_financial_tracker_mcp.tools.receipts import Receipts
from my_financial_tracker_mcp.tools.invoices import Invoices

from my_financial_tracker_mcp.database.receipts import ReceiptsDatabase
from my_financial_tracker_mcp.database.categories import CategoriesDatabase
from my_financial_tracker_mcp.database.invoices import InvoicesDatabase
from my_financial_tracker_mcp.database.financial_event import FinancialEventsDatabase

logger = logging.getLogger(__name__)

DB_FOLDER = os.getenv("DB_FOLDER")
DB_NAME = os.getenv("DB_NAME")
FILES_PATH = os.getenv("FILES_PATH")

# ──────────────────────────────────────────────────────────────────────────────
# Google OAuth2 helper
# ──────────────────────────────────────────────────────────────────────────────

#SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

DRIVE_CALENDAR_SCOPES  = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/calendar"]

gmail_creds = os.getenv("GOOGLE_CREDENTIALS_PATH")

receipts_database: ReceiptsDatabase
categories_database: CategoriesDatabase
invoices_database: InvoicesDatabase
financial_events_database: FinancialEventsDatabase

calendar_service: CalendarService
drive_service: DriveService
financial_event_service: FinancialEventsService

receipts: Receipts
invoices: Invoices
financial_events: FinancialEvents

web_service: Payments


# ──────────────────────────────────────────────────────────────────────────────
# MCP OAuth provider — consent page + optional disk persistence
# ──────────────────────────────────────────────────────────────────────────────

if _MCP_AUTH_ENABLED := bool(os.getenv("MCP_AUTH_TOKEN")):
    import secrets
    import time
    import urllib.parse
    from mcp.server.auth.provider import (
        AccessToken,
        AuthorizationCode,
        AuthorizationParams,
        RefreshToken,
        construct_redirect_uri,
    )
    from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
    from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
    from fastmcp.server.auth.providers.in_memory import InMemoryOAuthProvider

    class ConsentOAuthProvider(InMemoryOAuthProvider):
        """InMemoryOAuthProvider that redirects to a browser consent page before issuing codes."""

        def __init__(self, base_url: str) -> None:
            super().__init__(
                base_url=base_url,
                client_registration_options=ClientRegistrationOptions(
                    enabled=True, valid_scopes=["mcp:full"], default_scopes=["mcp:full"],
                ),
                revocation_options=RevocationOptions(enabled=True),
                required_scopes=["mcp:full"],
            )
            self._base_url = base_url.rstrip("/")
            self.pending: dict[str, tuple[OAuthClientInformationFull, AuthorizationParams]] = {}

        async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
            key = secrets.token_urlsafe(16)
            self.pending[key] = (client, params)
            return f"{self._base_url}/oauth/consent?key={urllib.parse.quote(key)}"

        def approve(self, key: str) -> str | None:
            item = self.pending.pop(key, None)
            if item is None:
                return None
            client, params = item
            scopes = params.scopes or []
            if client.scope:
                allowed = set(client.scope.split())
                scopes = [s for s in scopes if s in allowed]
            code_value = f"code_{secrets.token_hex(16)}"
            self.auth_codes[code_value] = AuthorizationCode(
                code=code_value,
                client_id=client.client_id or "",
                redirect_uri=params.redirect_uri,
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                scopes=scopes,
                expires_at=time.time() + 300,
                code_challenge=params.code_challenge,
            )
            return construct_redirect_uri(str(params.redirect_uri), code=code_value, state=params.state)

        def deny(self, key: str) -> str | None:
            item = self.pending.pop(key, None)
            if item is None:
                return None
            _, params = item
            return construct_redirect_uri(
                str(params.redirect_uri),
                error="access_denied",
                error_description="User denied access",
                state=params.state,
            )

    class PersistentOAuthProvider(ConsentOAuthProvider):
        """ConsentOAuthProvider that persists clients and tokens to a JSON file."""

        def __init__(self, base_url: str, state_path: Path) -> None:
            super().__init__(base_url=base_url)
            self._state_path = state_path
            self._load()

        def _load(self) -> None:
            if not self._state_path.exists():
                return
            try:
                data = json.loads(self._state_path.read_text())
                now = time.time()
                for cdata in data.get("clients", {}).values():
                    c = OAuthClientInformationFull.model_validate(cdata)
                    if c.client_id:
                        self.clients[c.client_id] = c
                for tdata in data.get("refresh_tokens", {}).values():
                    t = RefreshToken.model_validate(tdata)
                    self.refresh_tokens[t.token] = t
                for tdata in data.get("access_tokens", {}).values():
                    t = AccessToken.model_validate(tdata)
                    if t.expires_at is None or t.expires_at > now:
                        self.access_tokens[t.token] = t
                self._access_to_refresh_map.update(data.get("access_to_refresh", {}))
                self._refresh_to_access_map.update(data.get("refresh_to_access", {}))
                logger.info(
                    "OAuth state loaded from %s: %d client(s), %d access token(s), %d refresh token(s)",
                    self._state_path, len(self.clients), len(self.access_tokens), len(self.refresh_tokens),
                )
            except Exception as exc:
                logger.warning("OAuth state file %s unreadable (%s) — deleting and starting fresh", self._state_path, exc)
                try:
                    self._state_path.unlink()
                except OSError:
                    pass

        def _save(self) -> None:
            try:
                now = time.time()
                self._state_path.parent.mkdir(parents=True, exist_ok=True)
                data = {
                    "version": 1,
                    "clients": {cid: c.model_dump(mode="json") for cid, c in self.clients.items()},
                    "refresh_tokens": {tok: t.model_dump(mode="json") for tok, t in self.refresh_tokens.items()},
                    "access_tokens": {
                        tok: t.model_dump(mode="json")
                        for tok, t in self.access_tokens.items()
                        if t.expires_at is None or t.expires_at > now
                    },
                    "access_to_refresh": dict(self._access_to_refresh_map),
                    "refresh_to_access": dict(self._refresh_to_access_map),
                }
                self._state_path.write_text(json.dumps(data, indent=2))
            except Exception as exc:
                logger.warning("Failed to save OAuth state: %s", exc)

        async def register_client(self, client_info: OAuthClientInformationFull) -> None:
            await super().register_client(client_info)
            self._save()

        async def exchange_authorization_code(self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode) -> OAuthToken:
            token = await super().exchange_authorization_code(client, authorization_code)
            self._save()
            return token

        async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
            token = await super().exchange_refresh_token(client, refresh_token, scopes)
            self._save()
            return token

        async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
            await super().revoke_token(token)
            self._save()

    _OAUTH_STATE_PATH = Path(os.getenv("MCP_OAUTH_STATE_PATH") or (Path(__file__).parent.parent / "credentials" / "oauth_state.json"))
    _oauth_provider: PersistentOAuthProvider | None = PersistentOAuthProvider(
        base_url=f"http://localhost:{int(os.getenv('MCP_PORT', '8001'))}", state_path=_OAUTH_STATE_PATH
    )
else:
    _oauth_provider = None

# ──────────────────────────────────────────────────────────────────────────────
# Lifespan — shared state initialised once per server process
# fastmcp 3.x requires the lifespan to yield a dict[str, Any]
# Access in tools via: ctx.lifespan_context["key"]
# ──────────────────────────────────────────────────────────────────────────────

# Module-level reference to the lifespan dict — accessible from custom routes
# that don't have an MCP Context (e.g. /auth redirect).
_lifespan: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initialise shared state and make it available to every tool handler."""
    logger.info("Server starting — initialising Personal Finance System…")

    initialize()
    
    logger.info("Personal Finance System initialised")
    _lifespan.clear()
    try:
        yield _lifespan
    finally:
        logger.info("Server shutting down")

def initialize():
    global receipts_database
    global categories_database
    global invoices_database
    global financial_events_database

    global calendar_service
    global drive_service
    global financial_event_service

    global receipts
    global invoices
    global financial_events

    global web_service

    receipts_database = ReceiptsDatabase(folder_path=DB_FOLDER, db_name=DB_NAME)
    categories_database =  CategoriesDatabase(folder_path=DB_FOLDER, db_name=DB_NAME)
    invoices_database = InvoicesDatabase(folder_path=DB_FOLDER, db_name=DB_NAME)
    financial_events_database = FinancialEventsDatabase(folder_path=DB_FOLDER, db_name=DB_NAME)

    calendar_service = CalendarService()
    drive_service = DriveService()
    financial_event_service = FinancialEventsService(calendar_service, financial_events_database)

    receipts = Receipts(drive_service, receipts_database, categories_database)
    invoices = Invoices(drive_service, calendar_service, invoices_database, financial_event_service)
    financial_events = FinancialEvents(financial_event_service, financial_events_database)

    web_service = Payments(receipts_database, invoices_database, financial_event_service, calendar_service)


# ──────────────────────────────────────────────────────────────────────────────
# FastMCP instance — auth is enabled when MCP_AUTH_TOKEN is set
#
# When enabled, FastMCP adds full MCP spec OAuth 2.0 automatically:
#   GET /.well-known/oauth-authorization-server  — discovery metadata
#   POST /register                               — dynamic client registration
#   GET  /authorize                              — redirects to /oauth/consent
#   POST /token                                  — code → access+refresh tokens
#   POST /revoke                                 — token revocation
#
# MCP clients (Claude Code, VS Code, MCP Inspector) discover and complete the
# flow automatically — no manual bearer-token configuration needed.
# ──────────────────────────────────────────────────────────────────────────────

_INSTRUCTIONS = (
    "This server is a comprehensive Personal Finance Tracker. It manages three main workflows: "
    "1) Scanned Receipts: OCR-based extraction and archival. "
    "2) Transactions: Manual entry and semantic categorization of income/expenses. "
    "3) Invoices: Tracking of supplier/customer credits and debts with Google Calendar integration. "
    "SAFETY RULE: You must always use a two-step workflow for write operations: first call a 'prepare' tool, "
    "present the extracted data to the user for confirmation, and only then call the corresponding 'commit' tool."
)

mcp = FastMCP(
    name="my-financial-tracker-mcp",
    instructions=_INSTRUCTIONS,
    lifespan=lifespan,
    auth=_oauth_provider,
)


@mcp.tool(
    name="get_file_path",
    description="Get the default path of invoices/receipts",
    annotations={"readOnlyHint": True}
)
def get_file_path(
):
    return FILES_PATH


# ══════════════════════════════════════════════════════════════════════════════
# SECTION A½ — AUTHENTICATION TOOL
# ══════════════════════════════════════════════════════════════════════════════

# Shared state between the `authenticate` tool call and the /oauth/callback route.
# The tool blocks on `future`; the route handler sets the result when Google redirects back.
_pending_oauth: dict[str, Any] = {}

_TEMPLATES = Path(__file__).parent / "templates"
_OAUTH_SUCCESS_HTML = (_TEMPLATES / "gmail_success.html").read_text()


@mcp.custom_route("/oauth/callback", methods=["GET"])
async def oauth_callback(request: Request) -> Response:
    """Receive the Google OAuth2 redirect and exchange the code for a token."""
    if not _pending_oauth or "flow" not in _pending_oauth:
        return Response(
            "<html><body>No pending OAuth flow — call the <code>authenticate</code> "
            "tool first.</body></html>",
            media_type="text/html",
            status_code=400,
        )

    flow: Any = _pending_oauth["flow"]
    token_path: str = _pending_oauth["token_path"]
    lifespan_ctx: dict = _pending_oauth["lifespan"]

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as exc:
        logger.error("OAuth token exchange failed: %s", exc)
        return Response(f"Authentication failed: {exc}", status_code=500)
    finally:
        os.environ.pop("OAUTHLIB_INSECURE_TRANSPORT", None)

    # Persist token to disk only if GOOGLE_TOKEN_PERSISTENCY_PATH is explicitly set
    if token_path:
        p = Path(token_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(flow.credentials.to_json())

    # Hot-reload Gmail service into shared lifespan — no server restart needed
    from googleapiclient.discovery import build
    svc = build("gmail", "v1", credentials=flow.credentials)
    lifespan_ctx["gmail_service"] = svc
    profile = svc.users().getProfile(userId="me").execute()
    email = profile["emailAddress"]
    logger.info("Gmail authenticated as %s", email)

    # Notify the MCP client that the out-of-band elicitation is complete.
    # This uses the persistent GET SSE channel (stateful mode) — the spec-native
    # way to tell the client "the thing you were waiting for outside MCP is done".
    session = _pending_oauth.get("session")
    elicitation_id = _pending_oauth.get("elicitation_id")
    if session and elicitation_id:
        try:
            await session.send_elicit_complete(elicitation_id)
            logger.info("Sent notifications/elicitation/complete for %s", elicitation_id)
        except Exception as exc:
            logger.warning("Could not send elicitation/complete: %s", exc)

    _pending_oauth.clear()

    return Response(_OAUTH_SUCCESS_HTML, media_type="text/html")


# -------------------------
# RECEIPTS
# -------------------------

@mcp.tool(
    name="prepare_receipt",
    description="OCR + LLM structured extraction of receipts",
    annotations={"readOnlyHint": True}
)
async def prepare_receipt(
    image_path: str,
    description: str
):
    # search the default files folder calling get_file_path except if the user gives an alternative one
   return await receipts.prepare_receipt(image_path, description)
   
@mcp.tool(
    name="commit_receipt",
    description="Store receipts previously prepared",
    annotations={"readOnlyHint": False}
)
async def commit_receipt(
    data,
    timestamp: str,
    image_path: str
):
 return await receipts.commit_receipt(data, timestamp, image_path)

@mcp.tool(
    name="filter_receipts",
    description="Get existing receipts",
    annotations={"readOnlyHint": True}
)
async def filter_receipts(
        id:int = None, 
        start_date: str = None, 
        end_date: str = None
):
    return receipts.filter_receipts(id, start_date, end_date)

@mcp.tool(
    name="update_receipt",
    description="Update an existing receipt",
    annotations={"readOnlyHint": False}
)
async def update_receipt(
    id: int,
    description:str,
    company:str,
    amount: float,
    timestamp: str
):
    receipts.update_receipt(id, description, company, amount, timestamp)

# -------------------------
# TRANSACTION/ITEMS RELATED TO RECEIPTS
# -------------------------
@mcp.tool(
    name="prepare_transation",
    description="Prepare a manual transaction, a payment executed, a receipt-linked transaction and ask for a confirmation to the end user",
    annotations={"readOnlyHint": False}
)
async def prepare_transation(
    amount: float,
    description: str,
    company: str | None = None,
    timestamp: str | None = None
):
    return await receipts.prepare_transation(amount, description, company, timestamp)

@mcp.tool(
    name="commit_transaction",
    description="Only after the confirmation, save a prepared transaction, a payment executed, a receipt-linked transaction, you must recognise the category analysing the description",
    annotations={"readOnlyHint": False}
)
async def commit_transation(
    amount: float,
    description: str,
    company: str | None = None,
    timestamp: str | None = None,
    category: str | None = None
):
    return await receipts.commit_transation(amount, description, company, timestamp, category)


@mcp.tool(
    name="update_transaction",
    description="Update an existing transaction/item related to a receipt",
    annotations={"readOnlyHint": False}
)
async def update_transaction(
    id: int,
    amount: float,
    description: str,
    category: str
):

   return await receipts.update_receipt_item(id, amount, description, category)

@mcp.tool(
    name="get_transactions",
    description="Fetch transactions, details/items related to receipts, by optional filters",
    annotations={"readOnlyHint": True}
)
async def get_transactions(
    id: int = None,
    receipt_id: int = None,
    category: str = None,
    start_date: str = None,
    end_date: str = None,
):
    return await receipts.get_receipt_items(id, receipt_id, category, start_date, end_date)


@mcp.tool(
    name="add_receipt_item",
    description="Add a new receipt item",
    annotations={"readOnlyHint": False}
)
async def add_receipt_item(
    description: str,
    amount: float,
    category_id: float,
    receipt_id: int,
    category: str
):
    receipts.add_receipt_item(description, amount, category_id, receipt_id, category)

# -------------------------
# INVOICES
# -------------------------
@mcp.tool(
    name="prepare_invoice",
    description="OCR + LLM structured extraction of invoices",
    annotations={"readOnlyHint": True}
)
async def prepare_invoice(
    image_path: str,
    description: str = ""
):
  return await invoices.prepare_invoice(image_path, description)

@mcp.tool(
    name="commit_invoice",
    description="Store invoices previously prepared",
    annotations={"readOnlyHint": False}
)
async def commit_invoice(
    data,
    image_path: str
):
    return await invoices.commit_invoice(data, image_path)

@mcp.tool(
    name="update_invoice",
    description="Update an existing invoice",
    annotations={"readOnlyHint": False}
)
async def update_invoice(
    id: int,
    amount: float,
    incoming: bool,
    closed: bool
):
    invoices.update_invoice(id, amount, incoming, closed)


@mcp.tool(
    name="filter_invoices",
    description="Get existing invoices",
    annotations={"readOnlyHint": True}
)
async def filter_invoices(
        id:int = None, 
        incoming: bool = None,
        closed:bool = None, 
        start_date: str = None, 
        end_date: str = None
):
    return invoices.filter_invoices(id, incoming, closed, start_date, end_date)


# -------------------------
# ADD FUTURE PURCHASE TO DO
# -------------------------
@mcp.tool(
    name="add_future_purchase_to_calendar",
    description="Add a future payment or remind, never for payments already completed",
    annotations={"readOnlyHint": False}
)
async def add_future_purchase_to_calendar(
    title: str,
    amount: float,
    due_date: datetime
):
    return await financial_events.add_future_purchase_to_calendar(title, amount, due_date)

@mcp.tool(
    name="get_events",
    description="Return the list of events, future payments to execute",
    annotations={"readOnlyHint": True}
)
async def get_events(
    id: str,
    start_date: str,
    end_date: datetime
):
    return await financial_events.get_events(id, start_date, end_date)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION D — PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

@mcp.prompt()
def transactions_assistant() -> str:
    """
    Intelligent financial assistant for categorizing and storing personal transactions.

    GENERAL RULES:
    - Always use Italian language.
    - Never mix different languages in the same response.
    - Ask for confirmation before any write operation.
    - Keep responses concise and structured.

    You manage two financial entity types:

    1. SINGLE TRANSACTIONS (NO RECEIPT)
       Examples:
       - salary
       - bank transfer
       - cashback
       - refund
       - generic income or expense not linked to a receipt

       Workflow:
       - call prepare_transaction
       - ask user confirmation
       - call commit_transaction

       * note: an empty receipt is created and associated to it

    2. RECEIPTS
       Examples:
       - supermarket purchases
       - restaurant bills
       - retail shopping
       - OCR scanned receipts

       Workflow:
       - call prepare_receipt
       - ask user confirmation
       - call commit_receipt

       * note: the file is automatically stored in drive

    2. INVOICES
       Examples:
       - customer and supplier invoices (CREDITS/DEBTS)

       Workflow:
       - call prepare_invoice
       - ask user confirmation
       - call commit_invoice

       * note: the file is automatically stored in drive and added to google calendar

    CATEGORY RULES:
    - Always normalize categories.
    - Reuse existing categories when similar.
    - Avoid duplicate categories.
    - Prefer semantic similarity matching.

    RECEIPT EXTRACTION RULES:
    - Extract company name if available.
    - Extract receipt date if available.
    - Extract item breakdown when possible.
    - Generate a short meaningful description if missing.
    - Description max length: 20 characters.

    VALIDATION RULES:
    - Never create receipts for salaries or bank transfers.
    - Never commit data without explicit confirmation.

    INVOICES EXTRACTION RULES:
    - Extract company name if available, otherwise ask for it.
    - Extract emission date if available, otherwise ask for it.
    - Extract due date if available, otherwise ask for it.
    - Extract items when possible.
    - Generate a short meaningful description if missing.
    - Description max length: 20 characters.

    OUTPUT STYLE:
    - Keep responses structured.
    - Show transaction breakdown when multiple items exist.
    - Include receipt_id only for receipt-based operations.
    """

def build_category_prompt(description: str) -> str:
    return f"""
    You must detect the category associated to the description
    {description}
    """

# ══════════════════════════════════════════════════════════════════════════════
# Custom routes — registered on the mcp instance, served alongside /mcp
# ══════════════════════════════════════════════════════════════════════════════

@mcp.custom_route("/auth", methods=["GET"])
async def auth_redirect(request: Request) -> Response:
    """Redirect browser directly to the Google OAuth consent page.

    Simpler than copying the full URL — just open http://localhost:8001/auth.
    Requires GOOGLE_CREDENTIALS_PATH to be set.
    """
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    token_path = os.getenv("GOOGLE_TOKEN_PERSISTENCY_PATH")
    if not credentials_path or not Path(credentials_path).exists():
        return Response("GOOGLE_CREDENTIALS_PATH not set or file not found.", status_code=500)

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path, DRIVE_CALENDAR_SCOPES, autogenerate_code_verifier=False
    )
    flow.redirect_uri = str(request.url).replace("/auth", "/oauth/callback").split("?")[0]
    auth_url, _ = flow.authorization_url(access_type="offline")

    # Preserve session + elicitation_id set by gmail_authenticate (if called via tool)
    session = _pending_oauth.get("session")
    elicitation_id = _pending_oauth.get("elicitation_id")
    _pending_oauth.clear()
    _pending_oauth.update({
        "flow": flow,
        "token_path": token_path,
        "lifespan": _lifespan,
        "session": session,
        "elicitation_id": elicitation_id,
    })

    return RedirectResponse(auth_url)


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "version": "0.2.0"})


@mcp.custom_route("/auth-status", methods=["GET"])
async def auth_status(request: Request) -> JSONResponse:
    return JSONResponse({
        "gmail_configured": os.getenv("GOOGLE_CREDENTIALS_PATH") is not None,
        "mcp_auth_enabled": _MCP_AUTH_ENABLED,
    })


# ══════════════════════════════════════════════════════════════════════════════
# MCP OAuth consent page
# Shown when an MCP client redirects the user's browser to /authorize.
# ConsentOAuthProvider.authorize() redirects here; the Approve/Deny buttons
# POST back to complete or cancel the flow.  These routes are @custom_route
# so they bypass RequireAuthMiddleware — the user isn't authenticated yet.
# ══════════════════════════════════════════════════════════════════════════════

_CONSENT_HTML = (_TEMPLATES / "consent.html").read_text()
_CONSENT_EXPIRED_HTML = (_TEMPLATES / "consent_expired.html").read_text()


@mcp.custom_route("/oauth/consent", methods=["GET"])
async def oauth_consent_page(request: Request) -> Response:
    """Render the OAuth consent page for MCP client authorisation."""
    if _oauth_provider is None:
        return Response("MCP auth is not enabled.", status_code=404)
    key = request.query_params.get("key", "")
    item = _oauth_provider.pending.get(key)
    if item is None:
        return Response(_CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
    client, params = item
    client_name = client.client_name or client.client_id or "Unknown client"
    scopes = params.scopes or ["mcp:full"]
    return Response(_render_consent(key, client_name, scopes), media_type="text/html")


def _render_consent(key: str, client_name: str, scopes: list[str], error: str = "") -> str:
    scope_items = "".join(f"<li>{s}</li>" for s in scopes)
    error_html = f'<p class="error">{error}</p>' if error else ""
    return Template(_CONSENT_HTML).substitute(key=key, client_name=client_name, scope_items=scope_items, error_html=error_html)


@mcp.custom_route("/oauth/consent", methods=["POST"])
async def oauth_consent_action(request: Request) -> Response:
    """Handle Approve or Deny from the consent page."""
    if _oauth_provider is None:
        return Response("MCP auth is not enabled.", status_code=404)
    form = await request.form()
    key = str(form.get("key", ""))
    action = str(form.get("action", "deny"))

    if action == "deny":
        redirect_url = _oauth_provider.deny(key)
        if redirect_url is None:
            return Response(_CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
        return RedirectResponse(redirect_url, status_code=302)

    # Validate the server password before approving.
    entered = str(form.get("token", ""))
    expected = os.getenv("MCP_AUTH_TOKEN", "")
    if entered != expected:
        item = _oauth_provider.pending.get(key)
        if item is None:
            return Response(_CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
        client, params = item
        client_name = client.client_name or client.client_id or "Unknown client"
        scopes = params.scopes or ["mcp:full"]
        html = _render_consent(key, client_name, scopes, error="Incorrect password. Try again.")
        return Response(html, media_type="text/html", status_code=401)

    redirect_url = _oauth_provider.approve(key)
    if redirect_url is None:
        return Response(_CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
    return RedirectResponse(redirect_url, status_code=302)



# ══════════════════════════════════════════════════════════════════════════════
# App factory — called from __main__.py
# ══════════════════════════════════════════════════════════════════════════════

class _RegistrationCompatMiddleware:
    """Normalize POST /register for clients that omit refresh_token from grant_types.

    The MCP SDK requires both authorization_code and refresh_token. Some clients
    (e.g. Antigravity) only send authorization_code. This patches the body
    transparently before the SDK handler validates it.
    """

    def __init__(self, app: Any) -> None:
        self._app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") == "http" and scope.get("path") == "/register" and scope.get("method") == "POST":
            chunks: list[bytes] = []
            more = True
            while more:
                msg = await receive()
                chunks.append(msg.get("body", b""))
                more = msg.get("more_body", False)
            body = b"".join(chunks)

            try:
                data = json.loads(body)
                logger.debug("POST /register body: %s", json.dumps(data))
                grant_types: list[str] = data.get("grant_types", ["authorization_code", "refresh_token"])
                if isinstance(grant_types, list) and "authorization_code" in grant_types and "refresh_token" not in grant_types:
                    data["grant_types"] = grant_types + ["refresh_token"]
                    body = json.dumps(data).encode()
                    logger.info("RegistrationCompat: added refresh_token to grant_types for client %r",
                                data.get("client_name", "<unknown>"))
            except (json.JSONDecodeError, TypeError):
                pass

            delivered = False

            async def patched_receive() -> Any:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return {"type": "http.disconnect"}

            await self._app(scope, patched_receive, send)
        else:
            await self._app(scope, receive, send)

def build_app():
    """Build and return the ASGI application.

    MCP endpoint:    /mcp    (StreamableHTTP, stateful — GET SSE for notifications)
    OAuth endpoints: /.well-known/oauth-authorization-server, /authorize, /token, ...
    Consent page:    /oauth/consent   (open, no auth required)
    Health check:    /health          (open, no auth required)

    Auth is enabled when MCP_AUTH_TOKEN is set at process start.
    FastMCP handles all OAuth plumbing automatically via ConsentOAuthProvider.
    """
    app = mcp.http_app(path="/mcp", stateless_http=False)

    web_app = FastAPI()

    @web_app.get("/payments/confirm/purchase")
    async def confirm_purchase_payment(id: str):
        return await web_service.confirm_purchase_payment(id)

    @web_app.get("/payments/confirm/customer_invoice")
    async def confirm_customer_invoice_payment(id: str):
        return await web_service.confirm_customer_invoice_payment(id)

    @web_app.get("/payments/confirm/supplier_invoice")
    async def confirm_supplier_invoice_payment(id: str):
        return await web_service.confirm_supplier_invoice_payment(id)

    app.mount("/api", web_app)
    # Allow cross-origin requests from browser-based MCP clients.
    # - antigravity.google: Antigravity IDE (browser-based, makes XHR to /token)
    # - localhost / 127.0.0.1 any port: MCP Inspector and other local dev tools
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://antigravity.google"],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "mcp-session-id"],
        expose_headers=["mcp-session-id"],
    )
    if _MCP_AUTH_ENABLED:
        app = _RegistrationCompatMiddleware(app)
    return app
