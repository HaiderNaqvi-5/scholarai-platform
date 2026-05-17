import type { Metadata } from "next";
import { SystemErrorLayout } from "@/components/system/SystemErrorLayout";

export const metadata: Metadata = {
  title: "Page not found — AidwiseAI",
};

export default function NotFound() {
  return (
    <SystemErrorLayout
      title="We couldn't find that page."
      description="The link may be broken or the page may have moved."
      primary={{ href: "/feed", label: "Go to dashboard" }}
      secondary={{ href: "/upgrade", label: "See pricing" }}
    />
  );
}
