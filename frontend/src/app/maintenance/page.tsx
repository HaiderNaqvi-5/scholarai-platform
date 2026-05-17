import type { Metadata } from "next";
import { SystemErrorLayout } from "@/components/system/SystemErrorLayout";

export const metadata: Metadata = {
  title: "Maintenance — AidwiseAI",
};

/**
 * /maintenance — placeholder static page surfaced by ops via env flag or
 * middleware during a scheduled window. The end_time should be set at
 * deploy time (no live counter in v1; explicit window-end is what users
 * need).
 */
export default function Maintenance() {
  return (
    <SystemErrorLayout
      title="AidwiseAI is down for scheduled maintenance."
      description="We expect to be back shortly. Thanks for your patience."
      primary={{ href: "/", label: "Reload" }}
      secondary={{ label: "Email support", mailto: "support@aidwiseai.pk" }}
    />
  );
}
