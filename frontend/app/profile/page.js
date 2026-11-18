"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "../components/Sidebar";
import LogoutButton from "../components/LogoutButton";
import { createClient } from "@/lib/supabase/client";
import styles from "./page.module.css";

export default function ProfilePage() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    async function loadUser() {
      try {
        const supabase = createClient();
        const { data } = await supabase.auth.getUser();
        if (data?.user) {
          setUser(data.user);
        }
      } catch (err) {
        console.error("Error loading user profile:", err);
      }
    }
    loadUser();
  }, []);

  const fullName =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    (user?.email ? user.email.split("@")[0] : "LIA User");

  const email = user?.email || "Not connected yet";

  const isGoogle =
    user?.app_metadata?.provider === "google" ||
    user?.identities?.some((id) => id.provider === "google");

  const authMethod = isGoogle
    ? "Google OAuth"
    : user
    ? "Email & Password"
    : "Pending Setup";

  const avatarUrl =
    user?.user_metadata?.avatar_url || user?.user_metadata?.picture;

  return (
    <div className={styles.layout}>
      <Sidebar />

      <main className={styles.main}>
        <header className={styles.header}>
          <h2>My Profile</h2>
          <p>Manage your personal information and account preferences.</p>
        </header>

        <section className={styles.profileCard}>
          <div className={styles.profileHeader}>
            <div className={styles.avatar}>
              {avatarUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={avatarUrl}
                  alt={fullName}
                  referrerPolicy="no-referrer"
                  style={{
                    width: "100%",
                    height: "100%",
                    borderRadius: "50%",
                    objectFit: "cover",
                  }}
                />
              ) : (
                "👤"
              )}
            </div>

            <div className={styles.userInfo}>
              <h1>{fullName}</h1>
              <p>Land Intelligence AI Member</p>
              <span className={styles.accountStatus}>
                <span className={styles.statusDot}></span>
                {user ? "Active Account" : "Guest Mode"}
              </span>
            </div>
          </div>

          <div className={styles.divider}></div>

          <div className={styles.section}>
            <h2>Personal Information</h2>
            <p className={styles.sectionDescription}>
              Your account details and authentication provider.
            </p>

            <div className={styles.infoGrid}>
              <div className={styles.infoField}>
                <label>Full Name</label>
                <div>{fullName}</div>
              </div>

              <div className={styles.infoField}>
                <label>Email Address</label>
                <div>{email}</div>
              </div>

              <div className={styles.infoField}>
                <label>Account Type</label>
                <div>{user ? "Verified Member" : "Standard User"}</div>
              </div>

              <div className={styles.infoField}>
                <label>Authentication</label>
                <div>{authMethod}</div>
              </div>
            </div>
          </div>

          <div className={styles.divider}></div>

          <div className={styles.section}>
            <h2>Account Preferences</h2>

            <div className={styles.preference}>
              <div>
                <strong>Appearance</strong>
                <p>Customize your LIA experience.</p>
              </div>
              <span>Theme settings available in sidebar</span>
            </div>
          </div>

          <div
            className={styles.footer}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <p>
              {user ? (
                <>
                  Signed in as <strong>{email}</strong> via {authMethod}.
                </>
              ) : (
                "Sign in with Google or email to sync your data across sessions."
              )}
            </p>
            {user ? (
              <LogoutButton
                style={{
                  padding: "9px 18px",
                  borderRadius: "8px",
                  border: "1px solid var(--border-color)",
                  background: "var(--surface-bg)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                  fontWeight: "600",
                }}
              >
                Sign out
              </LogoutButton>
            ) : (
              <Link
                href="/login"
                style={{
                  padding: "9px 18px",
                  borderRadius: "8px",
                  background: "var(--emerald)",
                  color: "#ffffff",
                  fontSize: "13px",
                  fontWeight: "600",
                  textDecoration: "none",
                }}
              >
                Sign In
              </Link>
            )}
          </div>
        </section>

        <Link href="/dashboard" className={styles.backLink}>
          ← Back to New Chat
        </Link>
      </main>
    </div>
  );
}
