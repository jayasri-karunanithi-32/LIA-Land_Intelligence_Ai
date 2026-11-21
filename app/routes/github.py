"""
GitHub MCP Integration Routes for LIA.

Endpoints:
  GET  /github/status           — check if the current user has connected GitHub
  GET  /github/oauth/start      — redirect user to GitHub OAuth authorize page
  GET  /github/oauth/callback   — receive GitHub OAuth code, exchange for token, store it
  POST /github/connect/pat      — connect via Personal Access Token
  POST /github/disconnect       — remove stored GitHub credentials
  POST /github/mcp              — proxy MCP tool calls to GitHub MCP server
"""

import os
import logging
import secrets
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.github_store import (
    connection_status,
    save_connection,
    delete_connection,
    get_connection,
    ensure_table,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger("lia")

router = APIRouter(prefix="/github", tags=["GitHub MCP"])

# ---------------------------------------------------------------------------
# GitHub OAuth App credentials (set these in .env)
# ---------------------------------------------------------------------------
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

# Redirect URI registered in your GitHub OAuth App settings.
# In development: http://localhost:8000/github/oauth/callback
# In production:  https://<your-backend>/github/oauth/callback
GITHUB_REDIRECT_URI = os.getenv(
    "GITHUB_REDIRECT_URI", "http://localhost:8000/github/oauth/Callback"
)

# Frontend URL — where the backend redirects after OAuth completes.
FRONTEND_URL = os.getenv("NEXT_PUBLIC_FRONTEND_URL", "http://localhost:3000")

# GitHub OAuth scopes required for MCP tools.
GITHUB_SCOPES = "repo read:user read:org"

# GitHub MCP remote server endpoint.
GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"

# In-memory CSRF state store (per-process; acceptable for single-instance dev).
# In production with multiple instances use Redis or a DB column.
_oauth_states: dict[str, str] = {}  # state → user_id

# Ensure DB table exists at import time (safe, idempotent).
ensure_table()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class PATRequest(BaseModel):
    token: str


class MCPRequest(BaseModel):
    method: str
    params: Optional[dict] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fetch_github_user(token: str) -> dict:
    """
    Call GitHub REST API to fetch the authenticated user's profile.
    Returns a dict with at least 'login' and 'scopes'.
    Raises HTTPException on failure.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token is invalid or has insufficient permissions.",
        )
    data = resp.json()
    # 'x-oauth-scopes' header is present for OAuth tokens; PATs may omit it.
    scopes = resp.headers.get("x-oauth-scopes", "")
    return {"login": data.get("login", ""), "scopes": scopes}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/status")
async def github_status(current_user: dict = Depends(get_current_user)):
    """Return GitHub connection status for the authenticated LIA user."""
    user_id = current_user["user_id"]
    return connection_status(user_id)


@router.get("/oauth/start")
@router.post("/oauth/start")
async def github_oauth_start(
    request: Request,
    current_user: dict = Depends(get_current_user),
    format: Optional[str] = Query(None),
):
    """
    Initiate GitHub OAuth Web Application Flow.
    Generates a CSRF state token, stores the mapping, then redirects the
    user's browser to GitHub's authorization page (or returns {"url": ...} if JSON requested).
    """
    referer = request.headers.get("referer", "")
    frontend_origin = (
        "/".join(referer.split("/", 3)[:3])
        if (referer and "://" in referer)
        else FRONTEND_URL
    )

    if not GITHUB_CLIENT_ID:
        accept = request.headers.get("accept", "")
        if format == "json" or "application/json" in accept or request.method == "POST":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID in environment.",
            )
        return RedirectResponse(
            f"{frontend_origin}/plugins?github_error=github_oauth_not_configured_please_set_client_id"
        )

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "user_id": current_user["user_id"],
        "frontend_url": frontend_origin,
    }

    params = urlencode({
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": GITHUB_SCOPES,
        "state": state,
    })
    github_auth_url = f"https://github.com/login/oauth/authorize?{params}"

    accept = request.headers.get("accept", "")
    if format == "json" or "application/json" in accept or request.method == "POST":
        return {"url": github_auth_url}

    return RedirectResponse(github_auth_url)


@router.get("/oauth/Callback")
async def github_oauth_Callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    GitHub redirects here after the user grants (or denies) access.
    Exchanges the authorization code for an access token, validates it,
    then stores it encrypted in the database.
    Redirects the browser to the frontend plugins page.
    """
    state_data = _oauth_states.pop(state, None) if state else None
    if isinstance(state_data, dict):
        user_id = state_data.get("user_id")
        plugins_url = f"{state_data.get('frontend_url', FRONTEND_URL)}/plugins"
    else:
        user_id = state_data
        plugins_url = f"{FRONTEND_URL}/plugins"

    if error:
        logger.warning("GitHub OAuth denied by user: %s", error)
        return RedirectResponse(f"{plugins_url}?github_error={error}")

    if not code or not state:
        return RedirectResponse(f"{plugins_url}?github_error=missing_code_or_state")

    # CSRF validation.
    if user_id is None:
        logger.error("GitHub OAuth: invalid or replayed state token.")
        return RedirectResponse(f"{plugins_url}?github_error=invalid_state")

    # Exchange code for access token (server-side; secret never touches the browser).
    if not GITHUB_CLIENT_SECRET:
        return RedirectResponse(f"{plugins_url}?github_error=server_misconfigured")

    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
        )

    if token_resp.status_code != 200:
        logger.error("GitHub token exchange failed: %s", token_resp.text)
        return RedirectResponse(f"{plugins_url}?github_error=token_exchange_failed")

    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    if not access_token:
        err = token_data.get("error_description", "no_access_token")
        logger.error("GitHub did not return an access_token: %s", token_data)
        return RedirectResponse(f"{plugins_url}?github_error={err}")

    # Validate token and fetch user identity.
    try:
        gh_user = await _fetch_github_user(access_token)
    except HTTPException:
        return RedirectResponse(f"{plugins_url}?github_error=token_validation_failed")

    # Persist encrypted token.
    save_connection(
        user_id=user_id,
        token=access_token,
        login=gh_user["login"],
        method="oauth",
        scopes=gh_user["scopes"],
    )
    logger.info("GitHub OAuth connected for LIA user %s (GitHub: %s)", user_id, gh_user["login"])

    return RedirectResponse(f"{plugins_url}?github_connected=true")


@router.post("/connect/pat")
async def github_connect_pat(
    body: PATRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Connect a GitHub account via a Personal Access Token.
    The token is validated against the GitHub API before storage.
    The raw token is NEVER returned to the frontend.
    """
    if not body.token or not body.token.strip():
        raise HTTPException(status_code=400, detail="Token must not be empty.")

    token = body.token.strip()

    # Reject tokens that look like they aren't GitHub tokens.
    if not (token.startswith("ghp_") or token.startswith("github_pat_") or len(token) >= 20):
        raise HTTPException(
            status_code=400,
            detail="Token format is not recognised as a GitHub Personal Access Token.",
        )

    # Validate against GitHub API.
    gh_user = await _fetch_github_user(token)

    user_id = current_user["user_id"]
    save_connection(
        user_id=user_id,
        token=token,
        login=gh_user["login"],
        method="pat",
        scopes=gh_user["scopes"],
    )
    logger.info("GitHub PAT connected for LIA user %s (GitHub: %s)", user_id, gh_user["login"])

    return {
        "connected": True,
        "login": gh_user["login"],
        "method": "pat",
        "scopes": gh_user["scopes"],
    }


@router.post("/disconnect")
async def github_disconnect(current_user: dict = Depends(get_current_user)):
    """Remove the current user's GitHub connection."""
    user_id = current_user["user_id"]
    delete_connection(user_id)
    logger.info("GitHub disconnected for LIA user %s", user_id)
    return {"connected": False}


@router.post("/mcp")
async def github_mcp_proxy(
    body: MCPRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Proxy a JSON-RPC MCP tool call to the GitHub MCP remote server.

    The frontend sends:
        { "method": "tools/call", "params": { "name": "...", "arguments": {...} } }

    The backend appends the user's GitHub token from the database and
    forwards the request to https://api.githubcopilot.com/mcp/
    """
    user_id = current_user["user_id"]
    record = get_connection(user_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub is not connected. Connect your GitHub account first.",
        )

    mcp_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": body.method,
        "params": body.params or {},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GITHUB_MCP_URL,
            json=mcp_payload,
            headers={
                "Authorization": f"Bearer {record['token']}",
                "Accept": "application/json,text/event-stream",
                "Content-Type": "application/json",
            },
        )

    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token is expired or revoked. Please reconnect.",
        )

    if resp.status_code not in (200, 201, 202):
        logger.error("GitHub MCP error %d: %s", resp.status_code, resp.text[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub MCP server returned {resp.status_code}.",
        )

    return JSONResponse(content=resp.json(), status_code=200)
