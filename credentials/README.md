# Google API Credentials Setup

This directory holds OAuth2 credentials for the Google API (Google Drive, Google Calendar and Google Vision). **Never commit `credentials.json` or `token.json` to git** — they are excluded in `.gitignore`.

## Step-by-step setup

### 1. Create a Google Cloud project

1. Go to <https://console.cloud.google.com>
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Library**
4. Search for **Google Drive API** and click **Enable**
5. Search for **Google Calendar API** and click **Enable**
6. Search for **Cloud Vision API** and click **Enable**
6. Search for **Gemini API** and click **Enable**

### 2. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** (or Internal for Google Workspace)
3. Fill in the required fields: app name, support email, developer email
4. On the **Test users** page, add your Google account email
5. Save and continue through the remaining steps

### 3. Create OAuth 2.0 credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Choose **Desktop app** as the application type
4. Click **Create** then **Download JSON**
5. Google downloads a file named something like `client_secret_<id>.apps.googleusercontent.com.json`
6. **Rename it** and save as `credentials/credentials.json` in this project

### 4. GEMINI API Key
1. Navigate to https://aistudio.google.com/api-keys
2. Create an API Key associated to the project created on point 1.2
3. Copy && paste the key on GEMINI_API_KEY (to see section 6)

### 5. Google Drive folders
1. Create a folder to save receipts
2. Take note of its id and copy && past it on DRIVE_RECEIPTS_FOLDER (to see the section 6)
3. Create a folder to save invoices
4. Take note of its id and copy && past it on DRIVE_INVOICES_FOLDER (to see the section 6)

### 6. Configure environment variables
Copy the example file and fill in the paths:

```bash
cp .env.example .env
```

The relevant variables:

```bash
GOOGLE_CREDENTIALS_PATH=./credentials/credentials.json
GOOGLE_TOKEN_PERSISTENCY_PATH=./credentials/token.json

PUBLIC_BASE_URL = "localhost:8001"

GEMINI_API_KEY=
GEMINI_MODEL = "gemini-3-flash-preview"

# folders where to store invoices and receipts to process
DRIVE_INVOICES_FOLDER = "your folder id"
DRIVE_RECEIPTS_FOLDER = "your folder id"

# sqlite folder and file
DB_FOLDER = "./my_financial_tracker_mcp/database"
DB_NAME = "my_fin_trace.db"

# Default folder where invoices/receipts are kept for processing
FILES_PATH = "./my_financial_tracker_mcp/files"
```

### 5. First run — OAuth2 consent flow

* Start the server

```bash
cd ./my_financial_tracker_mcp 
uv sync
uv run mcp-server
```

* You will get a link into the shell to authenticate in google 
    - it occurs the first time and everytime the token is expired
    - the "token.pickle" file is created
    - remove this file and repeat this step every time you meet authentications errors
* Connect your agent to the MCP Server (In Antigravity by "Manage MCP Servers")


## Troubleshooting

**"Access blocked: This app's request is invalid"**
Add your Google account as a **Test user** in the OAuth consent screen (step 2 above).

**"redirect_uri_mismatch"**
Make sure you chose **Desktop app** (not Web application) as the credential type.

**Token expired / refresh error**
Delete `credentials/token.json` and restart the server to trigger a fresh consent flow.

**Wrong Google account signed in**
Delete `credentials/token.json` and restart — you'll be prompted to sign in again.

**Zone.Identifier files on Windows/WSL**
When downloading on Windows, a `filename:Zone.Identifier` sidecar file may appear.
It is harmless and ignored by Git — you can delete it or leave it.
