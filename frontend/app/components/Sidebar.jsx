
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import styles from "./Sidebar.module.css";
import ThemeToggle from "./ThemeToggle";
import { useRouter } from "next/navigation";

const navigation = [
  { name: "Chats", path: "/chats", icon: "💬" },
  { name: "Explore Area", path: "/explore", icon: "🧭" },
  { name: "Know Water Level", path: "/water-level", icon: "💧" },
  { name: "Plugins", path: "/plugins", icon: "🔌" }
];

export default function Sidebar({ onNewChat }) {
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      {collapsed && (
        <div
          className={styles.overlay}
          onClick={() => setCollapsed(false)}
        />
      )}
      <button
        className={`${styles.menuButton} ${collapsed ? styles.menuClosed : ""}`}
        onClick={() => setCollapsed(!collapsed)}
        aria-label="Toggle sidebar"
      >
        ☰
      </button>

      <aside className={`${styles.sidebar} ${collapsed ? styles.closed : ""}`}>

        <div className={styles.logo}>
          <span>🌿</span>
          <h2>LIA</h2>
        </div>

        <button
          className={styles.newChat}
          onClick={() => {
            onNewChat?.();
            router.push("/dashboard");
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
              className={`${styles.navLink} ${pathname === item.path ? styles.active : ""
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

          <Link
            href="/profile"
            className={styles.profile}
            onClick={() => setCollapsed(false)}
          >
            <span>👤</span>
            <div>
              <strong>LIA User</strong>
              <small>My Profile</small>
            </div>
          </Link>
        </div>
      </aside>
    </>
  );
}
