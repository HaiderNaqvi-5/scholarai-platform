import type { Metadata, Viewport } from "next";
import { Fraunces, Inter, JetBrains_Mono } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";

/**
 * Display — Fraunces.
 * Variable opsz + SOFT axes. Italic enabled by default on display h1.
 * Reserved for editorial moments: hero h1, page h1, scholarship name on detail,
 * tier titles on Pro+, blockquotes from policy docs. Not for inline emphasis.
 */
const display = Fraunces({
  subsets: ["latin"],
  /* When `axes` is set, weight must be "variable" — variable axes already cover the range. */
  weight: "variable",
  style: ["normal", "italic"],
  axes: ["opsz", "SOFT"],
  variable: "--font-display",
  display: "swap",
});

/**
 * Body — Inter.
 * Stylistic sets ss01 (single-storey a) + cv11 (tabular dotted zero) enabled
 * globally in globals.css `body { font-feature-settings }`.
 */
const ui = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ui",
  display: "swap",
});

/**
 * Data / mono — JetBrains Mono.
 * Codes, deadlines, currencies, IDs, keyboard shortcuts, file paths in admin.
 */
const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AidwiseAI — Funded master's, found for you.",
    template: "%s · AidwiseAI",
  },
  description:
    "AidwiseAI matches Pakistani students with fully-funded scholarships in the UK, US, Canada, Germany, and Australia. Build a Pakistan-context SOP, track applications, and practise the visa interview.",
  applicationName: "AidwiseAI",
  formatDetection: { telephone: false, email: false },
  metadataBase: new URL("https://aidwiseai.com"),
  openGraph: {
    type: "website",
    title: "AidwiseAI — Funded master's, found for you.",
    description:
      "Match against 47 universities, draft a Pakistan-context SOP, practise 70 visa questions.",
    siteName: "AidwiseAI",
  },
  twitter: {
    card: "summary_large_image",
    title: "AidwiseAI — Funded master's, found for you.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#FBF7EE",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${ui.variable} ${mono.variable}`}>
      <body className="bg-ivory text-ink-deep antialiased">
        <a href="#main" className="skip-to-content">
          Skip to content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
