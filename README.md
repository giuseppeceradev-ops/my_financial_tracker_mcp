# My Financial Tracker — MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server built with **FastMCP** for personal finance management. This system implements a stateful two-phase workflow (**Prepare → Commit**) integrating Google Vision OCR, Google Drive, and Google Calendar for the management of financial operations.

Project was implemented starting from https://github.com/The-Software-Academy/mcp-example/

[Advanced documentation](./my_financial_tracker_mcp/documentation/README.md)

[Video](https://drive.google.com/file/d/15GMiVcEvZCMLG3W0DmG0Q0VA7Eox6FK3/)

**Operations**
1. process of *single transactions* as purchases of single products (store on db)
2. process of *receipts* (recognise + OCR by google vision + google drive archiving + store in db) 
3. process of *invoices* active/passive (recognise + OCR by google vision + google drive archiving + google calendar + store in db) 
4. process of *future financial events* (reminders for future purchaces as google events)

## Quick introduction ##
| Feature | Implementation |
| :--- | :--- |
| **Tools — Core** | `get_file_path` (Returns the default location of examples of receipt/invoices) |
| **Tools — OCR & AI** | `prepare_receipt`, `prepare_invoice` (Data extraction via Google Vision + LLM) |
| **Tools — Transactions** | `prepare_transaction`, `commit_transaction`, `update_transaction`, `get_transactions` (Manual, executed, or receipt-linked entries with automated category recognition) |
| **Tools — Document Ops** | `commit_receipt`/`invoice`, `update_receipt`/`invoice`, `filter_receipts`/`invoices`, `add_receipt_item` (Full state management for processed documents) |
| **Tools — Scheduling** | `add_future_purchase_to_calendar` (Future payments/reminders only), `get_events` (List future payments to execute) |
| **Stateful Workflow** | Native **Prepare → User Confirmation → Commit** pattern |
| **Prompts** | `transactions_assistant`: Intelligent financial assistant (Italian logic) |
| **Lifespan** | Shared initialization of SQLite DBs and Google Services (Drive, Calendar) |
| **MCP OAuth 2.0** | `ConsentOAuthProvider`: Native auth with consent page and PKCE |
| **Custom Routes** | `/health`, `/auth`, `/oauth/callback`, `/api/payments/confirm/...` |
| **StreamableHTTP** | `stateless_http=False`: Persistent SSE channel for server-initiated notifications |

---

### Logic & Workflow Enhancements

1.  **Preparation Flow**: Documents and transactions are first "prepared" (`prepare_receipt`, `prepare_transaction`). This allows the user to review extracted data before persistence.
2.  **Categorization**: The `commit_transaction` tool includes logic to recognize the fiscal category by analyzing the description.
3.  **Temporal Separation**: 
    * `commit_transaction` handles completed payments.
    * `add_future_purchase_to_calendar` is reserved for future reminders/obligations.
4.  **Granular Control**: Tools like `add_receipt_item` and `update_transaction` allow for detailed modification of records after the initial OCR/Extraction phase.

---

## Configuration

Create a `.env` file in your root directory and configure the following variables:

| Variable | Purpose |
| :--- | :--- |
| `DB_FOLDER` | Path to the folder containing your SQLite databases |
| `DB_NAME` | Name of the database file (e.g., `finance.db`) |
| `FILES_PATH` | Default directory where receipts and invoices are stored |
| `GOOGLE_CREDENTIALS_PATH` | Path to your Google Cloud `credentials.json` |
| `MCP_AUTH_TOKEN` | Password for the MCP client consent page (Security) |
| `MCP_PORT` | Port for the HTTP server (Default: `8001`) |

---

## Tool Reference

### 1. Receipt Management
Used for immediate retail purchases.
*   **`prepare_receipt`**: Runs OCR on an image and proposes a structured data draft.
*   **`commit_receipt`**: Finalizes storage in the DB and archives the file to Google Drive.
*   **`filter_receipts`**: Search existing receipts by ID or date range.
*   **`add_receipt_item`**: Adds specific line-item details to an existing receipt.

### 2. Transactions & Categorization
Handles manual movements and semantic categorization.
*   **`prepare_transation`**: Creates a draft for a manual payment or receipt-linked movement.
*   **`commit_transaction`**: Persists the movement and automatically detects the category.
*   **`get_transactions`**: Query transactions by category, date, or receipt link.
*   **`update_transaction`**: Modifies amount, description, or category for existing records.

### 3. Invoice Management
Handles credits/debts (Clients/Suppliers) with deadline tracking.
*   **`prepare_invoice`**: Extracts supplier data, emission dates, and due dates via OCR.
*   **`commit_invoice`**: Saves the invoice, uploads to Drive, and creates a **Google Calendar** event.
*   **`filter_invoices`**: Query by status (open/closed) or type (incoming/outgoing).

### 4. Reminders & Events
*   **`add_future_purchase_to_calendar`**: Schedules a future payment reminder on Google Calendar.
*   **`get_events`**: Fetches a list of upcoming financial deadlines.

---

## AI Workflow: Transactions Assistant

The server includes a specialized prompt, `transactions_assistant`, which defines the behavior of the LLM:

*   **Language:** Commands and responses are processed in **Italian**.
*   **Safety Rule:** The assistant **must never** execute a `commit` tool without first showing the `prepare` results and receiving explicit user confirmation.
*   **Logic:** 
    *   Automatically distinguishes between "Single Transactions" (salaries, transfers) and "Receipts" (shopping, bills).
    *   Normalizes categories to prevent duplicates (e.g., "Grocery" and "Supermarket" merge).

---

## Security & OAuth 2.0

This server implements the full **MCP OAuth 2.0 spec**. When a client (like Claude Code or VS Code) connects:

1.  **Discovery:** The client finds auth endpoints via `/.well-known/oauth-authorization-server`.
2.  **Authorization:** The client redirects you to the `/oauth/consent` page.
3.  **Password:** You must enter the `MCP_AUTH_TOKEN` defined in your `.env` to approve the connection.
4.  **Google Integration:** The `/auth` route handles the secondary OAuth flow specifically for Google Services (Drive, Calendar, Vision).

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

*Note: This server is designed for personal financial tracking and requires an active Google Cloud Project with the Vision, Drive, and Calendar APIs enabled; it was tested with the AI agent included in Antigravity*
