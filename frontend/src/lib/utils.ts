import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDeadline(iso: string): { label: string; days: number; tone: "ok" | "soon" | "urgent" | "passed" } {
  const target = new Date(iso).getTime();
  const now = Date.now();
  const days = Math.ceil((target - now) / 86_400_000);
  if (days < 0) return { label: "Closed", days, tone: "passed" };
  if (days === 0) return { label: "Today", days, tone: "urgent" };
  if (days <= 7) return { label: `${days}d left`, days, tone: "urgent" };
  if (days <= 30) return { label: `${days}d left`, days, tone: "soon" };
  return { label: `${days}d left`, days, tone: "ok" };
}

export function formatAmount(amount: number | null | undefined, currency = "CAD"): string {
  if (amount == null) return "Amount varies";
  return new Intl.NumberFormat("en-CA", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
}
