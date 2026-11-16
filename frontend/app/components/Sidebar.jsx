
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import styles from "./Sidebar.module.css";
import ThemeToggle from "./ThemeToggle";

const navigation = [
  { name: "Chat", path: "/dashboard", icon: "💬" },
  { name: "Explore Area", path: "/explore", icon: "🧭" },
  { name: "Know Water Level", path: "/water-level", icon: "💧" },
];

export default function Sidebar({ onNewChat }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <button
        className={styles.menuButton}
        onClick={() => setCollapsed(!collapsed)}
        aria-label="Toggle sidebar"
      >
        ☰
      </button>

      {collapsed && (
        <div
          className={styles.overlay}
          onClick={() => setCollapsed(false)}
        />
      )}

      <aside className={`${styles.sidebar} ${collapsed ? styles.closed : ""}`}>
        <div className={styles.logo}>
          <span>🌿</span>
          <h2>LIA</h2>
        </div>

        <button
          className={styles.newChat}
          onClick={() => {
            onNewChat?.();
            setCollapsed(false);
          }}
        >
          <span>＋</span> New Chat
        </button>

        <nav className={styles.navigation}>
          {navigation.map((item) => (
            <Link
              key={item.path}
              href={item.path}
              onClick={() => setCollapsed(false)}
              className={`${styles.navLink} ${
                pathname === item.path ? styles.active : ""
              }`}
            >
              <span>{item.icon}</span>
              {item.name}
            </Link>
          ))}
        </nav>

        <div className={styles.bottom}>
          <ThemeToggle />

          <button className={styles.bottomLink}>⚙ Settings</button>

          <div className={styles.profile}>
            <span>👤</span>
            <div>
              <strong>LIA User</strong>
              <small>Land Intelligence AI</small>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
