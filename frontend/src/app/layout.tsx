import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Sora } from "next/font/google";

import { AuthProvider } from "@/components/auth/auth-provider";
import { ThemeProvider } from "@/components/theme/theme-provider";
import "./globals.css";

const displayFont = Sora({
  variable: "--font-display",
  subsets: ["latin"],
});

const uiFont = IBM_Plex_Sans({
  variable: "--font-ui",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const monoFont = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: {
    default: "ScholarAI — Scholarship Planning",
    template: "%s | ScholarAI",
  },
  description:
    "Find scholarships that fit your profile. ScholarAI combines a curated catalog with profile-aware recommendations and structured preparation tools.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="light">
      <body
        className={`${displayFont.variable} ${uiFont.variable} ${monoFont.variable} app-body`}
      >
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
