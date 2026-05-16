/**
 * Single source for the ISO-2 country codes the product cares about.
 * Pages should never declare their own per-page country list — pull from here
 * so visa setup, upgrade currency defaults, and the profile editor stay
 * consistent with the backend visa / scholarship dataset.
 */

import type { Currency } from "@/lib/api";

export type CountryCode = "PK" | "GB" | "US" | "CA" | "DE" | "AU" | "IE" | "NL" | "AE" | "FR";

/** Subset of CountryCode that the visa interview simulator supports. */
export type VisaCountry = "GB" | "US" | "CA" | "DE";

export type Country<C extends CountryCode = CountryCode> = {
  code: C;
  label: string;
  /** Default currency to anchor pricing for users billing from this country. */
  defaultCurrency: Currency;
};

/** Countries the visa interview simulator supports. Typed `VisaCountry`
 *  so consumers don't have to cast `code` back when wiring the API call. */
export const VISA_COUNTRIES: readonly Country<VisaCountry>[] = [
  { code: "GB", label: "United Kingdom", defaultCurrency: "GBP" },
  { code: "US", label: "United States (F-1)", defaultCurrency: "USD" },
  { code: "CA", label: "Canada", defaultCurrency: "USD" },
  { code: "DE", label: "Germany", defaultCurrency: "EUR" },
] as const;

/** All countries the product references in onboarding / matching. */
export const ALL_COUNTRIES: readonly Country[] = [
  { code: "PK", label: "Pakistan", defaultCurrency: "PKR" },
  ...VISA_COUNTRIES,
  { code: "AU", label: "Australia", defaultCurrency: "USD" },
  { code: "IE", label: "Ireland", defaultCurrency: "EUR" },
  { code: "NL", label: "Netherlands", defaultCurrency: "EUR" },
  { code: "AE", label: "United Arab Emirates", defaultCurrency: "AED" },
  { code: "FR", label: "France", defaultCurrency: "EUR" },
];

const _CURRENCY_BY_COUNTRY: Record<string, Currency> = Object.fromEntries(
  ALL_COUNTRIES.map((c) => [c.code, c.defaultCurrency]),
);

/** Backend `billing_country` → default Currency. PKR fallback for the Pakistan-first audience. */
export function defaultCurrencyForCountry(billingCountry: string | null | undefined): Currency {
  if (!billingCountry) return "PKR";
  return _CURRENCY_BY_COUNTRY[billingCountry.toUpperCase()] ?? "PKR";
}
