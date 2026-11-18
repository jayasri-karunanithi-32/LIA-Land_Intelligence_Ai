"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import GoogleAuthButton from "@/app/components/GoogleAuthButton";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawRedirect = searchParams.get("redirectedFrom") || searchParams.get("next") || "/dashboard";
  const destination =
    rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")
      ? rawRedirect
      : "/dashboard";

  const urlError = searchParams.get("error");
  const friendlyError =
    urlError === "access_denied"
      ? "Google sign-in was cancelled."
      : urlError
      ? decodeURIComponent(urlError.replace(/\+/g, " "))
      : "";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(friendlyError);

  async function handleLogin(e) {
    e.preventDefault();
    if (loading) return;

    setLoading(true);
    setError("");

    try {
      const supabase = createClient();
      const { data, error: signInError } =
        await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });

      if (signInError) throw signInError;

      if (data?.user) {
        router.replace(destination);
        router.refresh();
      }
    } catch (err) {
      setError(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "420px",
        background: "var(--surface-bg)",
        border: "1px solid var(--border-color)",
        borderRadius: "16px",
        padding: "36px 32px",
        boxShadow: "0 8px 30px rgba(0, 0, 0, 0.05)",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: "26px" }}>
        <Link
          href="/"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            textDecoration: "none",
            color: "var(--text-primary)",
            marginBottom: "12px",
          }}
        >
          <span style={{ fontSize: "28px" }}>🌿</span>
          <span style={{ fontSize: "24px", fontWeight: "700" }}>LIA</span>
        </Link>
        <h1
          style={{
            fontSize: "22px",
            color: "var(--text-primary)",
            marginBottom: "6px",
            fontWeight: "700",
          }}
        >
          Welcome Back
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
          Sign in to access your Land Intelligence dashboard
        </p>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            padding: "12px 14px",
            marginBottom: "20px",
            borderRadius: "10px",
            background: "rgba(227, 107, 107, 0.12)",
            border: "1px solid rgba(227, 107, 107, 0.3)",
            color: "#e36b6b",
            fontSize: "13px",
            lineHeight: "1.5",
          }}
        >
          {error}
        </div>
      )}

      {/* OAuth Integration: Google Sign-in */}
      <div style={{ marginBottom: "20px" }}>
        <GoogleAuthButton
          destination={destination}
          text="Continue with Google"
          onError={(msg) => setError(msg)}
        />
      </div>

      {/* Visual Divider */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            flex: 1,
            height: "1px",
            background: "var(--border-color)",
          }}
        />
        <span
          style={{
            fontSize: "12px",
            color: "var(--text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
          }}
        >
          or continue with email
        </span>
        <div
          style={{
            flex: 1,
            height: "1px",
            background: "var(--border-color)",
          }}
        />
      </div>

      <form
        onSubmit={handleLogin}
        style={{ display: "flex", flexDirection: "column", gap: "16px" }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <label
            htmlFor="email"
            style={{
              fontSize: "13px",
              fontWeight: "600",
              color: "var(--text-secondary)",
            }}
          >
            Email Address
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              padding: "12px 14px",
              borderRadius: "10px",
              border: "1px solid var(--border-color)",
              background: "var(--background)",
              color: "var(--text-primary)",
              outline: "none",
              fontSize: "14px",
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <label
            htmlFor="password"
            style={{
              fontSize: "13px",
              fontWeight: "600",
              color: "var(--text-secondary)",
            }}
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              padding: "12px 14px",
              borderRadius: "10px",
              border: "1px solid var(--border-color)",
              background: "var(--background)",
              color: "var(--text-primary)",
              outline: "none",
              fontSize: "14px",
            }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: "6px",
            padding: "13px",
            borderRadius: "10px",
            border: "none",
            background: "var(--emerald)",
            color: "#ffffff",
            fontWeight: "600",
            fontSize: "15px",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.7 : 1,
            transition: "opacity 0.2s",
          }}
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div
        style={{
          marginTop: "24px",
          textAlign: "center",
          fontSize: "13px",
          color: "var(--text-secondary)",
        }}
      >
        Don&apos;t have an account?{" "}
        <Link
          href="/signup"
          style={{
            color: "var(--emerald)",
            fontWeight: "600",
            textDecoration: "none",
          }}
        >
          Create account
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        background: "var(--background)",
      }}
    >
      <Suspense
        fallback={
          <div style={{ color: "var(--text-secondary)" }}>Loading...</div>
        }
      >
        <LoginForm />
      </Suspense>
    </main>
  );
}
