
"use client";

import { useTheme } from "./ThemeProvider";

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const isDark = theme === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label="Switch theme"
      style={{
        width: "100%",
        padding: "12px",
        borderRadius: "9px",
        border: "1px solid var(--border-color)",
        background: "var(--surface-bg)",
        color: "var(--text-primary)",
        display: "flex",
        alignItems: "center",
        gap: "12px",
        cursor: "pointer",
      }}
    >
      <span>{isDark ? "☀️" : "🌙"}</span>
      {isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
    </button>
  );
}
