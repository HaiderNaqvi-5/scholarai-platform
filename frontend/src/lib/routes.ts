export const appRoutes = [
  {
    href: "/",
    label: "Overview",
    description: "Product framing and the bounded MVP posture.",
    status: "foundation",
  },
  {
    href: "/onboarding",
    label: "Onboarding",
    description: "First-pass intake for the profile-to-recommendations slice.",
    status: "next",
  },
  {
    href: "/profile",
    label: "Profile",
    description: "Canonical student profile contract for eligibility checks.",
    status: "next",
  },
  {
    href: "/recommendations",
    label: "Recommendations",
    description: "Published scholarships ranked with rules-derived reasons.",
    status: "next",
  },
  {
    href: "/dashboard",
    label: "Dashboard",
    description: "Calm navigation surface for readiness and follow-up actions.",
    status: "reserved",
  },
  {
    href: "/document-feedback",
    label: "Document Feedback",
    description: "Reserved workflow for bounded, grounded writing assistance.",
    status: "deferred",
  },
  {
    href: "/interview",
    label: "Interview Practice",
    description: "Text-first rubric workflow with audio still deferred.",
    status: "deferred",
  },
] as const;
