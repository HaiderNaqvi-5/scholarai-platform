export type NavLink = {
  href: string;
  label: string;
  description?: string;
};

export type ProductRoute = NavLink & {
  section: "discovery" | "workspace" | "preparation" | "account" | "admin";
  requiresAuth?: boolean;
};

export const marketingNavLinks: NavLink[] = [
  {
    href: "/scholarships",
    label: "Scholarships",
    description: "Browse the published scholarship catalog.",
  },
  {
    href: "/#how-it-works",
    label: "How it works",
    description: "Understand the GrantPath AI workflow.",
  },
];

export const appNavRoutes: ProductRoute[] = [
  {
    href: "/scholarships",
    label: "Scholarships",
    description: "Explore the published scholarship catalog.",
    section: "discovery",
  },
  {
    href: "/recommendations",
    label: "Recommendations",
    description: "Review profile-aware scholarship matches.",
    section: "workspace",
    requiresAuth: true,
  },
  {
    href: "/dashboard",
    label: "Dashboard",
    description: "Keep saved opportunities and next actions in one place.",
    section: "workspace",
    requiresAuth: true,
  },
  {
    href: "/document-feedback",
    label: "Documents",
    description: "Improve application writing with bounded guidance.",
    section: "preparation",
    requiresAuth: true,
  },
  {
    href: "/interview",
    label: "Interview",
    description: "Practice structured scholarship interview responses.",
    section: "preparation",
    requiresAuth: true,
  },
];

export const accountRoutes: ProductRoute[] = [
  {
    href: "/onboarding",
    label: "Onboarding",
    description: "Set up the minimum profile needed for recommendations.",
    section: "account",
    requiresAuth: true,
  },
  {
    href: "/profile",
    label: "Profile",
    description: "Review and update your recommendation inputs.",
    section: "account",
    requiresAuth: true,
  },
  {
    href: "/curation",
    label: "Curation",
    description: "Review records and publish validated scholarship data.",
    section: "admin",
    requiresAuth: true,
  },
];

export const landingFeatureRoutes: ProductRoute[] = [
  {
    href: "/scholarships",
    label: "Discovery",
    description: "Search a Canada-first scholarship corpus with structured filters.",
    section: "discovery",
  },
  {
    href: "/recommendations",
    label: "Prioritization",
    description: "Review explainable matches once a profile is on file.",
    section: "workspace",
    requiresAuth: true,
  },
  {
    href: "/document-feedback",
    label: "Preparation",
    description: "Improve writing and interview readiness with bounded coaching.",
    section: "preparation",
    requiresAuth: true,
  },
];
