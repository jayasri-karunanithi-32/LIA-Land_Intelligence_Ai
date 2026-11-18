
"use client";

import Sidebar from "../components/Sidebar";
import styles from "./page.module.css";

export default function ChatsPage() {
  return (
    <div className={styles.layout}>
      <Sidebar />

      <main className={styles.main}>
        <header className={styles.header}>
          <h2>Chats</h2>
          <p>Your conversations with LIA, all in one place.</p>
        </header>

        <section className={styles.content}>
          <div className={styles.illustration}>
            <div className={styles.iconCircle}>
              <span>💬</span>
              <span className={styles.sparkle}>✦</span>
            </div>
          </div>

          <h1>Your conversations, all in one place.</h1>

          <p className={styles.description}>
            We're working on bringing chat history to LIA.
            Soon, you'll be able to revisit your previous
            conversations and continue where you left off.
          </p>

          <div className={styles.status}>
            <span className={styles.statusDot}></span>
            Chat history coming soon
          </div>

          <a href="/dashboard" className={styles.button}>
            <span>＋</span> Start a New Chat
          </a>
        </section>
      </main>
    </div>
  );
}
