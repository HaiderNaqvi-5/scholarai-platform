import type { Metadata } from "next";
import { SystemErrorLayout } from "@/components/system/SystemErrorLayout";

export const metadata: Metadata = {
  title: "Access denied — AidwiseAI",
};

export default function Denied() {
  return (
    <SystemErrorLayout
      title="You don&rsquo;t have access to that."
      description="If you think this is wrong, email support@aidwiseai.pk and include the page you were trying to open."
      primary={{ href: "/feed", label: "Go to dashboard" }}
      secondary={{ label: "Email support", mailto: "support@aidwiseai.pk" }}
    />
  );
}
