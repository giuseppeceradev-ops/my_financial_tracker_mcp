"""Entry point for the Gmail MCP server.

Usage:
    uv run mcp-server           Start the HTTP MCP server (default port 8001)

Gmail authentication is handled via the gmail_authenticate tool — no separate
auth command needed. Run the server, connect your MCP client, and call
gmail_authenticate to complete the Google OAuth2 flow in-session.
"""
from __future__ import annotations

import logging
import os

from google import genai

import click


@click.command()
@click.option("--port", "-p", type=int, default=None, help="HTTP port (default: $MCP_PORT or 8001)")
@click.option("--host", "-H", type=str, default="0.0.0.0", help="Bind host")
@click.option("-v", "--verbose", count=True, help="Verbosity: -v INFO, -vv DEBUG")
def main(port: int | None, host: str, verbose: int) -> None:
    """Start the Gmail MCP server (StreamableHTTP transport)."""
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbose, logging.DEBUG)
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY missing")

    client = genai.Client(api_key=api_key)
    
    import uvicorn
    from my_financial_tracker_mcp.server import build_app

    effective_port = port or int(os.getenv("MCP_PORT", "8001"))
    app = build_app()

    click.echo(f"Starting MCP server on http://{host}:{effective_port}/mcp")
    if os.getenv("MCP_AUTH_TOKEN"):
        click.echo("MCP OAuth ENABLED — clients discover auth automatically via /.well-known/oauth-authorization-server")
    gmail_creds = os.getenv("GMAIL_CREDENTIALS_PATH")
    click.echo(f"Gmail: {'CONFIGURED' if gmail_creds else 'not configured (demo tools only)'}")
    click.echo(f"Connect your MCP client to http://localhost:{effective_port}/mcp/")

    uvicorn.run(
    app,
    host=host,
    port=effective_port,
    log_level="info"
)


if __name__ == "__main__":
    main()
