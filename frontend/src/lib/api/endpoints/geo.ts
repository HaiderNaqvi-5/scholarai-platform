import { api } from "../client";
import type { Currency } from "../types";

export type GeoCurrencyResponse = {
  currency: Currency;
  country: string | null;
};

export const geo = {
  /** GET /geo/currency — public, no auth. Backend proxies ipwho.is with
   * 1h Redis cache, returns supported Currency code or PKR fallback. */
  currency: () =>
    api.get<GeoCurrencyResponse>("/geo/currency", { auth: false }),
};
