"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import GoogleAuthButton from "@/app/components/GoogleAuthButton";

function SignupForm() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  async function handleSignup(e) {
    e.preventDefault();
    if (loading) return;

    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setErrorMessage("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const supabase = createClient();
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: {
            full_name: fullName.trim(),
          },
          emailRedirectTo: `${origin}/auth/callback?next=/dashboard`,
        },
      });

      if (error) {
        throw error;
      }

      if (data?.session) {
        router.replace("/dashboard");
        router.refresh();
      } else {
        setSuccessMessage(
          "Account created! Please check your email inbox to verify your account before logging in."
        );
      }
    } catch (err) {
      setErrorMessage(err.message || "Failed to create account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "440px",
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
          Create an Account
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
          Start exploring land and area intelligence with LIA
        </p>
      </div>

      {errorMessage && (
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
          {errorMessage}
        </div>
      )}

      {successMessage ? (
        <div style={{ textAlign: "center", padding: "10px 0" }}>
          <div
            style={{
              padding: "16px",
              borderRadius: "12px",
              background: "rgba(117, 201, 155, 0.15)",
              border: "1px solid var(--emerald)",
              color: "var(--emerald)",
              fontSize: "14px",
              lineHeight: "1.6",
              marginBottom: "24px",
            }}
          >
            {successMessage}
          </div>
          <Link
            href="/login"
            style={{
              display: "inline-block",
              padding: "12px 24px",
              borderRadius: "10px",
              background: "var(--emerald)",
              color: "#ffffff",
              fontWeight: "600",
              textDecoration: "none",
              fontSize: "14px",
            }}
          >
            Go to Sign In
          </Link>
        </div>
      ) : (
        <>
          {/* OAuth Integration: Google Sign-up */}
          <div style={{ marginBottom: "20px" }}>
            <GoogleAuthButton
              destination="/dashboard"
              text="Sign up with Google"
              onError={(msg) => setErrorMessage(msg)}
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
              or sign up with email
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
            onSubmit={handleSignup}
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <label
                htmlFor="fullName"
                style={{
                  fontSize: "13px",
                  fontWeight: "600",
                  color: "var(--text-secondary)",
                }}
              >
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                required
                autoComplete="name"
                placeholder="Your name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
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
                autoComplete="new-password"
                placeholder="At least 6 characters"
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

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <label
                htmlFor="confirmPassword"
                style={{
                  fontSize: "13px",
                  fontWeight: "600",
                  color: "var(--text-secondary)",
                }}
              >
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                required
                autoComplete="new-password"
                placeholder="Repeat your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
              {loading ? "Creating account..." : "Sign Up"}
            </button>
          </form>
        </>
      )}

      <div
        style={{
          marginTop: "24px",
          textAlign: "center",
          fontSize: "13px",
          color: "var(--text-secondary)",
        }}
      >
        Already have an account?{" "}
        <Link
          href="/login"
          style={{
            color: "var(--emerald)",
            fontWeight: "600",
            textDecoration: "none",
          }}
        >
          Sign in
        </Link>
      </div>
    </div>
  );
}

export default function SignupPage() {
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
        <SignupForm />
      </Suspense>
    </main>
  );
}
