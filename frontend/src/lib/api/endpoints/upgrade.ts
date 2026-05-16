import { api } from "../client";
import type {
  Currency,
  PricingResponse,
  WaitlistJoinRequest,
  WaitlistJoinResponse,
} from "../types";

export const upgrade = {
  /** GET /upgrade/pricing — public, no auth required. */
  pricing: (currency: Currency = "PKR") =>
    api.get<PricingResponse>("/upgrade/pricing", {
      query: { currency },
      auth: false,
    }),
  /** POST /waitlist — public; no Stripe, just lead capture. */
  joinWaitlist: (body: WaitlistJoinRequest) =>
    api.post<WaitlistJoinResponse>("/waitlist", body, { auth: false }),
};
