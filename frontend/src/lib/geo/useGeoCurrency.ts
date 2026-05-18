"use client";

import { useEffect, useState } from "react";
import type { Currency } from "@/lib/api";
import { defaultCurrencyForCountry } from "@/lib/countries";

const CACHE_KEY = "aidwise.geo_currency";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
const SUPPORTED: readonly Currency[] = ["PKR", "GBP", "EUR", "AED", "USD"];

type Source = "cache" | "geo" | "fallback" | "initial";

type Cached = { currency: Currency; country?: string | null; ts: number };

type State = { currency: Currency; country: string | null; source: Source };

function isSupported(value: string): value is Currency {
  return (SUPPORTED as readonly string[]).includes(value);
}

function readCache(): Cached | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Cached;
    if (typeof parsed?.ts !== "number") return null;
    if (Date.now() - parsed.ts > CACHE_TTL_MS) return null;
    if (!isSupported(parsed.currency)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeCache(value: Cached): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(CACHE_KEY, JSON.stringify(value));
  } catch {
    /* storage quota or disabled */
  }
}

/**
 * Detect the visitor's currency from their IP via ipwho.is.
 * Falls back to PKR (Pakistan-first audience) on any error. Cached 24h
 * in localStorage so repeat visits skip the network round-trip.
 */
export function useGeoCurrency(initial: Currency = "PKR"): State {
  const [state, setState] = useState<State>(() => {
    const cached = readCache();
    if (cached) {
      return {
        currency: cached.currency,
        country: cached.country ?? null,
        source: "cache",
      };
    }
    return { currency: initial, country: null, source: "initial" };
  });

  useEffect(() => {
    if (state.source === "cache" || state.source === "geo") return;
    const controller = new AbortController();
    let cancelled = false;

    (async () => {
      try {
        const r = await fetch("https://ipwho.is/?fields=success,country_code,currency", {
          signal: controller.signal,
          cache: "no-store",
        });
        if (!r.ok) throw new Error(`ipwho ${r.status}`);
        const j: {
          success?: boolean;
          country_code?: string;
          currency?: { code?: string };
        } = await r.json();
        if (j.success === false) throw new Error("ipwho lookup failed");

        const code = (j.currency?.code ?? "").toUpperCase();
        const cc = (j.country_code ?? "").toUpperCase();
        const detected: Currency = isSupported(code)
          ? code
          : defaultCurrencyForCountry(cc);

        if (cancelled) return;
        const next: State = {
          currency: detected,
          country: cc || null,
          source: "geo",
        };
        setState(next);
        writeCache({ currency: detected, country: cc || null, ts: Date.now() });
      } catch {
        if (cancelled) return;
        setState((prev) => ({ ...prev, source: "fallback" }));
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [state.source]);

  return state;
}
