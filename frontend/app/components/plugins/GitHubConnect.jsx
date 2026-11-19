"use client";

import { useState, useEffect, useCallback } from "react";
import "./GitHubConnect.css";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Retrieves the Supabase JWT from the browser session cookie/localStorage
 * so we can pass it as a Bearer token to the FastAPI backend.
 */
async function getSupabaseToken() {
  const { createClient } = await import("@/lib/supabase/client");
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token || null;
}

async function apiFetch(path, options = {}) {
  const token = await getSupabaseToken();
  if (!token) throw new Error("Not authenticated. Please log in first.");

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export default function GitHubConnect({ onClose }) {
  const [view, setView] = useState("menu"); // 'menu' | 'pat' | 'connected'
  const [status, setStatus] = useState(null); // null | { connected, login, method, scopes }
  const [pat, setPat] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [patVisible, setPatVisible] = useState(false);

  // ── Load current connection status ──────────────────────────────────────
  const fetchStatus = useCallback(async () => {
    try {
      const data = await apiFetch("/github/status");
      setStatus(data);
      if (data.connected) setView("connected");
    } catch {
      setStatus({ connected: false });
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // ── Check URL params for OAuth result (after GitHub redirect) ──────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("github_connected") === "true") {
      // Clean the URL and reload status
      window.history.replaceState({}, "", window.location.pathname);
      fetchStatus();
    }
    if (params.get("github_error")) {
      const msg = params.get("github_error").replace(/_/g, " ");
      setError(`GitHub OAuth failed: ${msg}`);
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [fetchStatus]);

  // ── OAuth flow — open backend redirect ───────────────────────────────────
  async function handleOAuth() {
    setError("");
    setLoading(true);
    try {
      const token = await getSupabaseToken();
      if (!token) throw new Error("Not authenticated.");
      // The backend /github/oauth/start is a GET redirect, so we navigate directly.
      // We pass the auth token as a query param because the browser won't send
      // the Authorization header on a redirect. The backend route reads it.
      window.location.href = `${API_BASE}/github/oauth/start?access_token=${token}`;
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  // ── PAT submission ────────────────────────────────────────────────────────
  async function handlePATSubmit(e) {
    e.preventDefault();
    setError("");
    if (!pat.trim()) {
      setError("Please enter your Personal Access Token.");
      return;
    }
    setLoading(true);
    try {
      const data = await apiFetch("/github/connect/pat", {
        method: "POST",
        body: JSON.stringify({ token: pat.trim() }),
      });
      setStatus(data);
      setView("connected");
      setPat("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // ── Disconnect ────────────────────────────────────────────────────────────
  async function handleDisconnect() {
    setLoading(true);
    setError("");
    try {
      await apiFetch("/github/disconnect", { method: "POST" });
      setStatus({ connected: false });
      setView("menu");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="gh-overlay" role="dialog" aria-modal="true" aria-label="GitHub Connect">
      <div className="gh-modal">
        {/* Header */}
        <div className="gh-header">
          <div className="gh-header-left">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/github.png" alt="" className="gh-logo" />
            <span className="gh-title">Connect GitHub</span>
          </div>
          <button className="gh-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {/* Error banner */}
        {error && (
          <div className="gh-error" role="alert">
            {error}
          </div>
        )}

        {/* ── Menu view ── */}
        {view === "menu" && (
          <div className="gh-body">
            <p className="gh-desc">
              Connect your GitHub account to give LIA access to your
              repositories, issues, and pull requests through the GitHub MCP
              server.
            </p>

            <div className="gh-actions">
              <button
                className="gh-btn gh-btn-primary"
                onClick={handleOAuth}
                disabled={loading}
              >
                <svg className="gh-gh-icon" viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
                </svg>
                Continue with GitHub
              </button>

              <div className="gh-divider">
                <span>or</span>
              </div>

              <button
                className="gh-btn gh-btn-secondary"
                onClick={() => setView("pat")}
                disabled={loading}
              >
                Connect with Personal Access Token
              </button>
            </div>
          </div>
        )}

        {/* ── PAT view ── */}
        {view === "pat" && (
          <div className="gh-body">
            <button
              className="gh-back"
              onClick={() => { setView("menu"); setError(""); }}
            >
              ← Back
            </button>

            <p className="gh-desc">
              Enter a GitHub Personal Access Token (classic or fine-grained).
              Required scopes: <code>repo</code>, <code>read:user</code>,{" "}
              <code>read:org</code>.
            </p>

            <form onSubmit={handlePATSubmit} className="gh-form">
              <label className="gh-label" htmlFor="pat-input">
                Personal Access Token
              </label>
              <div className="gh-pat-row">
                <input
                  id="pat-input"
                  type={patVisible ? "text" : "password"}
                  className="gh-input"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  value={pat}
                  onChange={(e) => setPat(e.target.value)}
                  autoComplete="off"
                  spellCheck={false}
                />
                <button
                  type="button"
                  className="gh-toggle-vis"
                  onClick={() => setPatVisible((v) => !v)}
                  aria-label={patVisible ? "Hide token" : "Show token"}
                >
                  {patVisible ? "Hide" : "Show"}
                </button>
              </div>

              <a
                href="https://github.com/settings/tokens/new?scopes=repo,read:user,read:org&description=LIA+MCP+Integration"
                target="_blank"
                rel="noopener noreferrer"
                className="gh-link"
              >
                Generate a new token on GitHub ↗
              </a>

              <button
                type="submit"
                className="gh-btn gh-btn-primary"
                disabled={loading}
              >
                {loading ? "Connecting…" : "Connect"}
              </button>
            </form>
          </div>
        )}

        {/* ── Connected view ── */}
        {view === "connected" && status?.connected && (
          <div className="gh-body">
            <div className="gh-connected-badge">
              <span className="gh-dot" />
              Connected
            </div>

            <div className="gh-info">
              <div className="gh-info-row">
                <span className="gh-info-label">GitHub account</span>
                <span className="gh-info-value">@{status.login}</span>
              </div>
              <div className="gh-info-row">
                <span className="gh-info-label">Auth method</span>
                <span className="gh-info-value">
                  {status.method === "oauth" ? "GitHub OAuth" : "Personal Access Token"}
                </span>
              </div>
              {status.scopes && (
                <div className="gh-info-row">
                  <span className="gh-info-label">Scopes</span>
                  <span className="gh-info-value gh-scopes">{status.scopes}</span>
                </div>
              )}
            </div>

            <p className="gh-desc gh-mcp-note">
              LIA can now use GitHub MCP tools: list repositories, read issues,
              create pull requests, search code, and more — using your
              GitHub permissions.
            </p>

            <button
              className="gh-btn gh-btn-danger"
              onClick={handleDisconnect}
              disabled={loading}
            >
              {loading ? "Disconnecting…" : "Disconnect GitHub"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
