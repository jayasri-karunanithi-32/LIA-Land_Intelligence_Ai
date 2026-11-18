
"use client";

import Link from "next/link";
import Sidebar from "../components/Sidebar";
import styles from "./page.module.css";

export default function ProfilePage() {
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
            <div className={styles.avatar}>👤</div>

            <div className={styles.userInfo}>
              <h1>LIA User</h1>
              <p>Land Intelligence AI Member</p>
              <span className={styles.accountStatus}>
                <span className={styles.statusDot}></span>
                Active Account
              </span>
            </div>
          </div>

          <div className={styles.divider}></div>

          <div className={styles.section}>
            <h2>Personal Information</h2>
            <p className={styles.sectionDescription}>
              Your account details will appear here.
            </p>

            <div className={styles.infoGrid}>
              <div className={styles.infoField}>
                <label>Full Name</label>
                <div>LIA User</div>
              </div>

              <div className={styles.infoField}>
                <label>Email Address</label>
                <div>Not connected yet</div>
              </div>

              <div className={styles.infoField}>
                <label>Account Type</label>
                <div>Standard User</div>
              </div>

              <div className={styles.infoField}>
                <label>Authentication</label>
                <div>Pending Setup</div>
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

          <div className={styles.footer}>
            <p>
              Profile editing and account management will be
              available after authentication integration.
            </p>
          </div>
        </section>

        <Link href="/dashboard" className={styles.backLink}>
          ← Back to New Chat
        </Link>
      </main>
    </div>
  );
}
