import type { Metadata } from "next";
import { SystemErrorLayout } from "@/components/system/SystemErrorLayout";

export const metadata: Metadata = {
  title: "Offline — AidwiseAI",
};

export default function Offline() {
  return (
    <SystemErrorLayout
      title="You&rsquo;re offline."
      description="AidwiseAI needs a connection to load matches, tracker, and documents. Changes you make in queued forms will sync when you reconnect."
      primary={{ href: "/", label: "Try again" }}
      secondary={{ href: "/feed", label: "Go to dashboard" }}
    />
  );
}
