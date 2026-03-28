"use client";

import { useTheme } from "@/components/theme/theme-provider";

export function ThemeToggle() {
  const { isMounted, theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      aria-label={isMounted ? `Switch to ${isDark ? "light" : "dark"} mode` : "Toggle theme"}
      className="nav-link nav-link--quiet theme-toggle"
      onClick={toggleTheme}
      type="button"
    >
      <span aria-hidden="true" className="theme-toggle__icon">
        {isMounted ? (isDark ? "☀️" : "🌙") : "◐"}
      </span>
      <span className="theme-toggle__text">
        {isMounted ? (isDark ? "Light mode" : "Dark mode") : "Theme"}
      </span>
    </button>
  );
}
