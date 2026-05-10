export { api, ApiError, API_BASE_URL, getTokens, setTokens, subscribeTokens } from "./client";
export * from "./types";

import { auth } from "./endpoints/auth";
import { profile } from "./endpoints/profile";
import { scholarships } from "./endpoints/scholarships";
import { recommendations } from "./endpoints/recommendations";
import { saved } from "./endpoints/saved";
import { documents } from "./endpoints/documents";
import { interviews } from "./endpoints/interviews";
import { curation } from "./endpoints/curation";
import { mentors } from "./endpoints/mentors";
import { accessControl } from "./endpoints/access-control";
import { analytics } from "./endpoints/analytics";

export const endpoints = {
  auth,
  profile,
  scholarships,
  recommendations,
  saved,
  documents,
  interviews,
  curation,
  mentors,
  accessControl,
  analytics,
};
