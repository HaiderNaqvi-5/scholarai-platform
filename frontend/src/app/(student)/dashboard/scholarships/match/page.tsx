/**
 * Alias route — spec §3.1 IA names this `/dashboard/scholarships/match`
 * while the working implementation lives at `/scholarships`. Re-export
 * the same default so both URLs resolve identically. Sidebar +
 * onboarding redirect target this path.
 */
export { default } from "@/app/(student)/scholarships/page";
