export type AppRoute = {
  href: string;
  label: string;
  title: string;
  summary: string;
  showInNav: boolean;
  showInLanding: boolean;
};

export const APP_ROUTES: AppRoute[] = [
  {
    href: "/",
    label: "Landing",
    title: "Landing page",
    summary:
      "A calm editorial entrypoint that introduces ScholarAI without default startup-template patterns.",
    showInNav: true,
    showInLanding: false,
  },
  {
    href: "/onboarding",
    label: "Onboarding",
    title: "Onboarding",
    summary:
      "A step-oriented entry flow that frames what the product needs before profile completion.",
    showInNav: true,
    showInLanding: true,
  },
  {
    href: "/profile",
    label: "Profile",
    title: "Profile",
    summary:
      "A structured profile capture route reserved for the academic, target, and supporting signals used by ranking.",
    showInNav: true,
    showInLanding: true,
  },
  {
    href: "/recommendations",
    label: "Recommendations",
    title: "Recommendations",
    summary:
      "A recommendation review surface for fit, eligibility, and explanation-driven next actions.",
    showInNav: true,
    showInLanding: true,
  },
  {
    href: "/dashboard",
    label: "Dashboard",
    title: "Dashboard",
    summary:
      "An application-planning workspace for upcoming deadlines, tracked scholarships, and execution state.",
    showInNav: true,
    showInLanding: true,
  },
  {
    href: "/document-feedback",
    label: "Documents",
    title: "Document feedback",
    summary:
      "A bounded SOP feedback route reserved for scholarship-writing assistance rather than a general content studio.",
    showInNav: true,
    showInLanding: true,
  },
  {
    href: "/interview-practice",
    label: "Interview",
    title: "Interview practice",
    summary:
      "A text-first interview-prep route for question, answer, and rubric-feedback scaffolding.",
    showInNav: true,
    showInLanding: true,
  },
];
