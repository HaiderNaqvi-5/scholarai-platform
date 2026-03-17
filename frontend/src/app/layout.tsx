import type { Metadata } from "next";
import { Geist_Mono, Outfit } from "next/font/google";

import { AuthProvider } from "@/components/auth/auth-provider";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
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
    <html lang="en">
      <body
        className={`${outfit.variable} ${geistMono.variable} app-body`}
      >
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
