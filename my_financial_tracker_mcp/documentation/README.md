# My Financial Tracker MCP

Advanced MCP server for personal financial management with OCR, AI workflows, Google Workspace integrations, and stateful financial orchestration.

Project implemented starting from https://github.com/The-Software-Academy/mcp-example/

---

# Table of Contents

1. Introduction
2. Main Features
3. System Architecture
4. AI Workflow Model
5. Project Structure
6. Utility Tools
7. Receipt Management
8. Transaction Management
9. Invoice Management
10. Financial Events
11. REST API
12. AI Prompts
13. OAuth & Authentication
14. MCP Compatibility Middleware
15. Google Integrations
16. Database Layer
17. Security Model
18. Environment Variables Configuration
19. Installation
20. Server Startup
21. Available Endpoints
22. MCP Compatibility
23. Current Limitations

---

# Introduction

**My Financial Tracker MCP** is a comprehensive MCP (Model Context Protocol) server built with **FastMCP 3.x** for intelligent financial management.

The project combines:

* OCR document analysis
* structured AI extraction
* semantic transaction categorization
* stateful AI workflows
* payment reminders
* Google Workspace integrations
* MCP-native OAuth authentication

The primary goal of the project is to provide an nfrastructure capable of:

* understanding financial documents
* categorizing expenses automatically
* orchestrating reminders and payments
* maintaining a queryable financial history through MCP

---

# Main Features

## Receipt Management

Supports:

* Google Vision OCR
* AI structured extraction
* automatic parsing of:

  * amounts
  * dates
  * company names
  * line items
* automatic Google Drive archival
* receipt item management

Workflow:

```text
prepare_receipt
    ↓
user confirmation
    ↓
commit_receipt
```

---

## Transaction Management

Supports:

* manual expenses
* bank transfers
* salaries
* cashback
* refunds
* standalone transactions

Features:

* AI semantic categorization
* automatic empty receipt association
* filtering
* transaction editing

Workflow:

```text
prepare_transation
    ↓
user confirmation
    ↓
commit_transaction
```

---

## Invoice Management

Supports:

* customer invoices
* supplier invoices
* debt/credit tracking
* automatic reminders
* Google Calendar synchronization
* Google Drive archival

Workflow:

```text
prepare_invoice
    ↓
user confirmation
    ↓
commit_invoice
```

---

## Financial Events

Automated handling of:

* future payments
* reminders
* notifications
* due dates

Integrated with:

* Google Calendar
* REST APIs

---

## Full MCP OAuth Support

Implements:

* MCP OAuth 2.0 specification
* Dynamic Client Registration
* refresh token support
* persistent token storage
* custom consent screens
* stateful SSE notifications

Compatible with:

* Antigravity (Currently I've only tested it)

---

# System Architecture

## Technology Stack

| Component      | Technology          |
| -------------- | ------------------- |
| MCP Server     | FastMCP 3.x         |
| ASGI Framework | FastAPI / Starlette |
| Database       | SQLite              |
| OCR            | Google Vision API   |
| Storage        | Google Drive API    |
| Calendar       | Google Calendar API |
| AI Extraction  | Gemini              |
| Authentication | OAuth 2.0 MCP       |

---

# AI Workflow Model

## "Prepare → Confirm → Commit"

All write operations strictly follow the pattern:

```text
prepare
    ↓
user confirmation
    ↓
commit
```

This guarantees:

* operational safety
* human validation
* AI error prevention
* full control over persisted data

---

# Project Structure

```text
my_financial_tracker_mcp/
│
├── database/
├── services/
├── tools/
├── web_services/
├── templates/
├── credentials/
│
├── __main__.py
└── server.py
```

---

# Utility Tools

---

## get_file_path

Returns the default path for:

* receipts
* invoices
* OCR documents

### Type

```python
readOnlyHint = True
```

---

# Receipt Management

---

## prepare_receipt

Performs:

* Google Vision OCR
* AI parsing
* structured extraction

### Parameters

| Parameter   | Type |
| ----------- | ---- |
| image_path  | str  |
| description | str  |

### Output

```json
{
  "company": "...",
  "amount": 0,
  "timestamp": "...",
  "items": []
}
```

---

## commit_receipt

Persists a previously prepared receipt.

### Parameters

| Parameter  | Type   |
| ---------- | ------ |
| data       | object |
| timestamp  | str    |
| image_path | str    |

---

## filter_receipts

Fetches existing receipts.

### Filters

* id
* start_date
* end_date

---

## update_receipt

Updates receipt metadata.

---

## add_receipt_item

Adds items to an existing receipt.

---

# Transaction Management

---

## prepare_transation

Prepares a manual transaction.

### Parameters

| Parameter   | Type  |
| ----------- | ----- |
| amount      | float |
| description | str   |
| company     | str   |
| timestamp   | str   |

---

## commit_transaction

Persists a transaction.

### Features

* AI categorization
* category normalization
* automatic associations

---

## update_transaction

Updates existing transactions.

---

## get_transactions

Fetches transactions using filters.

### Available Filters

* id
* receipt_id
* category
* date range

---

# Invoice Management

---

## prepare_invoice

OCR + AI extraction for invoices.

### Features

* date detection
* amount extraction
* company extraction
* due date extraction
* line item extraction

---

## commit_invoice

Persists invoices.

### Automations

* Google Drive upload
* Google Calendar reminders

---

## update_invoice

Updates:

* amount
* incoming/outgoing status
* payment status

---

## filter_invoices

Queries invoices using:

* id
* incoming
* closed
* date filters

---

# Financial Events

---

## add_future_purchase_to_calendar

Adds future payment reminders.

### Parameters

| Parameter | Type     |
| --------- | -------- |
| title     | str      |
| amount    | float    |
| due_date  | datetime |

---

## get_events

Returns reminders and due events.

---

# REST API

## Payment Confirmation Endpoints

```http
GET /api/payments/confirm/purchase
```

```http
GET /api/payments/confirm/customer_invoice
```

```http
GET /api/payments/confirm/supplier_invoice
```

---

# AI Prompts

---

## transactions_assistant

Main AI prompt used by the financial workflow assistant.

### Main Rules

* Italian language only
* confirmation required before writes
* concise structured responses
* semantic categorization

---

## build_category_prompt

Helper prompt for semantic categorization.

---

# OAuth & Authentication

---

## OAuth Features

The server implements:

* Authorization Code Flow
* Refresh Token Flow
* Dynamic Client Registration
* Custom Consent UI
* Token revocation

---

## OAuth Endpoints

| Endpoint                                | Description          |
| --------------------------------------- | -------------------- |
| /authorize                              | start authorization  |
| /token                                  | token exchange       |
| /register                               | dynamic registration |
| /revoke                                 | token revocation     |
| /.well-known/oauth-authorization-server | discovery metadata   |

---

## ConsentOAuthProvider

Custom OAuth provider implementing:

* consent screen rendering
* server password validation
* MCP scope management

---

## PersistentOAuthProvider

Persistent OAuth provider extension with:

* token persistence
* refresh token storage
* client persistence

---

# MCP Compatibility Middleware

---

## _RegistrationCompatMiddleware

Compatibility layer for MCP clients that omit:

```json
"refresh_token"
```

inside grant types.

Compatible with:

* Antigravity
* legacy MCP clients

---

# Google Integrations

---

## Google Drive

Used for:

* receipt archival
* invoice archival

---

## Google Calendar

Used for:

* reminders
* future payments
* notifications

---

## Google Vision

Used for:

* document OCR
* receipt scanning
* invoice scanning

---

# Database Layer

The system uses SQLite with separated persistence layers:

| Database Layer          | Responsibility |
| ----------------------- | -------------- |
| ReceiptsDatabase        | receipts       |
| CategoriesDatabase      | categories     |
| InvoicesDatabase        | invoices       |
| FinancialEventsDatabase | events         |

---

# Security Model

## Core Safety Rules

The system:

* never persists data without confirmation
* uses stateful workflows
* implements standard MCP OAuth
* supports token revocation
* separates authentication and consent

---

# Environment Variables Configuration

The server uses a `.env` file for configuring:

* Google integrations
* MCP OAuth
* database
* filesystem
* AI extraction
* networking

---

# Full Example

```env
# ── Google API (OAuth2) ─────────────────────────────────────────────────────────

# OAuth credentials downloaded from Google Cloud Console
GOOGLE_CREDENTIALS_PATH=./credentials/credentials.json

# Google OAuth token persistence
GOOGLE_TOKEN_PERSISTENCY_PATH=./credentials/token.json

# Google Vision OCR service account
GOOGLE_APPLICATION_CREDENTIALS=./credentials/vision-key.json


# ── MCP Server ────────────────────────────────────────────────────────────────

# MCP server listening port
MCP_PORT=8001

# Password required in the MCP OAuth consent page.
# Empty → authentication disabled.
MCP_AUTH_TOKEN=

# MCP OAuth persistence:
# registered clients + refresh tokens
MCP_OAUTH_STATE_PATH=./credentials/oauth_state.json

# Elicitation mode:
# empty → fail closed
# 1     → fail open
MCP_ELICITATION_FAIL_OPEN=1


# ── Gemini AI ─────────────────────────────────────────────────────────────────

# Gemini API key
GEMINI_API_KEY=

# AI model used by the system
GEMINI_MODEL=gemini-3-flash-preview


# ── Google Drive ──────────────────────────────────────────────────────────────

# Google Drive folder for invoices
DRIVE_INVOICES_FOLDER=your_google_drive_folder_id

# Google Drive folder for receipts
DRIVE_RECEIPTS_FOLDER=your_google_drive_folder_id


# ── Public URL ────────────────────────────────────────────────────────────────

# Public server URL used for OAuth callbacks
PUBLIC_BASE_URL=localhost:8001


# ── Database ──────────────────────────────────────────────────────────────────

# SQLite database directory
DB_FOLDER=./my_financial_tracker_mcp/database

# SQLite database name
DB_NAME=my_fin_trace.db


# ── File Processing ───────────────────────────────────────────────────────────

# Default folder for receipts/invoices processing
FILES_PATH=./my_financial_tracker_mcp/files
```

---

# Environment Variables Reference

---

## GOOGLE_CREDENTIALS_PATH

Google OAuth2 credentials file.

Required for:

* Google Drive
* Google Calendar

---

## GOOGLE_TOKEN_PERSISTENCY_PATH

Stores:

* Google access tokens
* Google refresh tokens

Allows persistent authentication.

---

## GOOGLE_APPLICATION_CREDENTIALS

Google Vision OCR service account credentials.

Required for:

* receipt OCR
* invoice OCR

---

## MCP_PORT

HTTP server port.

Default:

```text
8001
```

---

## MCP_AUTH_TOKEN

Enables MCP OAuth authentication.

If configured:

* OAuth is enabled
* consent pages are shown
* access and refresh tokens are issued

If empty:

* local development mode
* authentication disabled

---

## MCP_OAUTH_STATE_PATH

Stores MCP OAuth state:

* registered clients
* refresh tokens
* access tokens

Deleting the file forces all clients to re-authenticate.

---

## MCP_ELICITATION_FAIL_OPEN

Controls destructive tool fallback behavior.

### Fail-closed mode

```env
MCP_ELICITATION_FAIL_OPEN=
```

The tool fails if elicitation is unsupported.

### Fail-open mode

```env
MCP_ELICITATION_FAIL_OPEN=1
```

The tool proceeds without confirmation.

Not recommended for production.

---

## GEMINI_API_KEY

Gemini API key used for:

* AI extraction
* semantic categorization
* document parsing

---

## GEMINI_MODEL

Gemini model used by the system.

Example:

```env
GEMINI_MODEL=gemini-3-flash-preview
```

---

## DRIVE_INVOICES_FOLDER

Google Drive folder ID used for:

* invoice archival

---

## DRIVE_RECEIPTS_FOLDER

Google Drive folder ID used for:

* receipt archival

---

## PUBLIC_BASE_URL

Public URL used for:

* OAuth callbacks
* browser redirects

---

## DB_FOLDER

SQLite database directory.

---

## DB_NAME

SQLite database name.

---

## FILES_PATH

Default document processing folder used for:

* OCR
* invoice scanning
* receipt scanning

---

## Quick Start

1. COnfigure your google account and enable for google drive, google vision and google calendar. Set creadentials as explained in [Credentials setup](../../credentials/README.md)

2. Set the .env files (to see ./.env.example)

3.  **Install Dependencies**:
    ```bash
    uv sync

4.  **Run the Server:**
    ```bash
    uv run mcp-server

5. if it is the first time that you start the server, you will get a google auth link into the terminal. Click on it to authenticate google services.

6. Server MCP is required to be authenticated. If you are using Antigravity it is enough to use "Manage MCP Servers"

7.  **Verify Status**:
    Check the health endpoint at `http://localhost:8001/health`.



---

# Available Endpoints

| Endpoint        | Description    |
| --------------- | -------------- |
| /mcp            | MCP endpoint   |
| /auth           | Google login   |
| /oauth/callback | OAuth callback |
| /oauth/consent  | consent page   |
| /health         | health check   |
| /auth-status    | auth status    |

---

# MCP Compatibility

Compatible with:

* Antigravity

---

# Current Limitations

The project is experimental and not production-ready.
