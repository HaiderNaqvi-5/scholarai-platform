export const appRoutes = [
  {
    href: "/",
    label: "Overview",
    description: "Product framing and the bounded MVP posture.",
    status: "foundation",
  },
  {
    href: "/scholarships",
    label: "Scholarships",
    description: "Public browse and detail views for published scholarship records.",
    status: "active",
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
    description: "Authenticated workspace for saved opportunities and next actions.",
    status: "active",
  },
  {
    href: "/document-feedback",
    label: "Document Feedback",
    description: "Text-first SOP and essay feedback with bounded grounded guidance.",
    status: "active",
  },
  {
    href: "/interview",
    label: "Interview Practice",
    description: "Text-first practice sessions with rubric scoring and structured feedback.",
    status: "active",
  },
] as const;
