export const THEME_STORAGE_KEY = "scholarai.theme";

export type Theme = "light" | "dark";

function isTheme(value: string): value is Theme {
  return value === "light" || value === "dark";
}

export function readStoredTheme(): Theme | null {
  if (typeof window === "undefined") {
    return null;
  }

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (!storedTheme || !isTheme(storedTheme)) {
    return null;
  }

  return storedTheme;
}

export function writeStoredTheme(theme: Theme) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(THEME_STORAGE_KEY, theme);
}
