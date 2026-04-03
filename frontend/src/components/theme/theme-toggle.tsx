"use client";

import { useTheme } from "@/components/theme/theme-provider";

type IconProps = {
  className?: string;
};

function SunIcon({ className }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} fill="none" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="3.5" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M10 2.5V4.5M10 15.5V17.5M17.5 10H15.5M4.5 10H2.5M15.3033 4.6967L13.8891 6.1109M6.1109 13.8891L4.6967 15.3033M15.3033 15.3033L13.8891 13.8891M6.1109 6.1109L4.6967 4.6967"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function MoonIcon({ className }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} fill="none" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M13.9148 13.9148C10.8702 16.9594 5.93387 16.9594 2.88927 13.9148C0.8992 11.9247 0.19557 9.0817 0.77837 6.47408C0.90522 5.90665 1.62139 5.72029 2.04477 6.11557C4.99083 8.86697 9.6108 8.80622 12.483 5.934C13.5322 4.88473 14.2706 3.62428 14.6892 2.27586C14.8653 1.70843 15.5816 1.50377 16.0328 1.8852C16.1307 1.96794 16.2269 2.05385 16.3211 2.14311C19.3657 5.18771 19.3657 10.124 16.3211 13.1686C15.5444 13.9454 14.6942 14.5274 13.7998 14.9149"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function ThemeNeutralIcon({ className }: IconProps) {
  return (
    <svg aria-hidden="true" className={className} fill="none" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
      <path d="M10 2.5V17.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

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
        {!isMounted ? (
          <ThemeNeutralIcon className="theme-toggle__icon-svg" />
        ) : isDark ? (
          <SunIcon className="theme-toggle__icon-svg" />
        ) : (
          <MoonIcon className="theme-toggle__icon-svg" />
        )}
      </span>
      <span className="theme-toggle__text">
        {isMounted ? (isDark ? "Light mode" : "Dark mode") : "Theme"}
      </span>
    </button>
  );
}
