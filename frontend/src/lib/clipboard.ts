/**
 * Browser clipboard + file-download helpers. Centralised so every "copy" /
 * "download as .txt" button toasts identically and we don't sprinkle Blob /
 * URL.createObjectURL boilerplate across pages.
 */

import { toast } from "sonner";

export async function copyText(text: string, label = "Copied to clipboard."): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(label);
  } catch {
    toast.error("Couldn't copy.");
  }
}

export function downloadText(filename: string, text: string, mime = "text/plain"): void {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
  } finally {
    URL.revokeObjectURL(url);
  }
}
