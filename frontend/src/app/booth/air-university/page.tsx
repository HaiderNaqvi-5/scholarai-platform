import { redirect } from "next/navigation";

/**
 * Air University booth (May 2026 exhibition) — locked.
 *
 * We did not attend the exhibition. Page kept on disk for future-cohort
 * rebrand; redirect prevents public discovery in the meantime. Delete
 * this stub when the next exhibition lands and restore from git history.
 */
export default function BoothPage() {
  redirect("/");
}
