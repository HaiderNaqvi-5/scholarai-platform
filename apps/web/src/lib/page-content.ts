type PlaceholderContent = {
  eyebrow: string;
  title: string;
  summary: string;
  metrics: Array<{ label: string; value: string }>;
  primaryActionLabel: string;
  secondaryActionLabel: string;
  detailCards: Array<{ title: string; body: string }>;
  placeholderList: string[];
};

export const PAGE_CONTENT: Record<string, PlaceholderContent> = {
  onboarding: {
    eyebrow: "Student setup",
    title: "Onboarding route scaffold",
    summary:
      "This route reserves the first-run flow that sets expectations, captures intent, and guides students into profile completion with minimal friction.",
    metrics: [
      { label: "Mode", value: "step flow" },
      { label: "Priority", value: "MVP critical" },
      { label: "Tone", value: "calm and clear" },
    ],
    primaryActionLabel: "Primary step action",
    secondaryActionLabel: "Secondary support action",
    detailCards: [
      {
        title: "Progress framing",
        body: "The eventual UI should make next steps obvious without using dashboard noise or dense status widgets.",
      },
      {
        title: "Expectation setting",
        body: "Copy should explain why ScholarAI needs profile detail before recommendations become useful.",
      },
    ],
    placeholderList: [
      "entry messaging and value framing",
      "step progress scaffold",
      "empty, validation, and completion states",
    ],
  },
  profile: {
    eyebrow: "Profile foundation",
    title: "Profile route scaffold",
    summary:
      "This route reserves the student profile form for the academic, target-country, and supporting signals needed by eligibility and recommendation logic.",
    metrics: [
      { label: "Layout", value: "sectioned form" },
      { label: "Density", value: "restrained" },
      { label: "Data", value: "student owned" },
    ],
    primaryActionLabel: "Save profile state",
    secondaryActionLabel: "Return later",
    detailCards: [
      {
        title: "Signal capture",
        body: "Profile inputs should map cleanly to documented recommendation and eligibility fields without introducing speculative form sections.",
      },
      {
        title: "Form rhythm",
        body: "The final build should use one-column mobile flow and calm spacing rather than compressed enterprise-form patterns.",
      },
    ],
    placeholderList: [
      "personal and academic sections",
      "target program and geography sections",
      "save, validation, and completion states",
    ],
  },
  recommendations: {
    eyebrow: "Decision support",
    title: "Recommendations route scaffold",
    summary:
      "This route reserves the list view for published scholarships, explanation cues, and the next actions students should take after ranking review.",
    metrics: [
      { label: "Output", value: "fit-oriented" },
      { label: "Authority", value: "validated data" },
      { label: "Pattern", value: "list plus filters" },
    ],
    primaryActionLabel: "View ranked opportunities",
    secondaryActionLabel: "Adjust filters",
    detailCards: [
      {
        title: "Explanation-first UI",
        body: "The final surface should foreground why a scholarship appears instead of leaning on oversized score badges.",
      },
      {
        title: "Filter restraint",
        body: "Filters should stay concise, quiet, and reversible, with mobile-ready drawer behavior rather than permanent control walls.",
      },
    ],
    placeholderList: [
      "filter drawer or sidebar region",
      "ranked result cards",
      "empty, stale, and no-results states",
    ],
  },
  dashboard: {
    eyebrow: "Execution workspace",
    title: "Dashboard route scaffold",
    summary:
      "This route reserves the application-planning workspace for tracked scholarships, next deadlines, and status changes after discovery.",
    metrics: [
      { label: "Focus", value: "planning" },
      { label: "Primary", value: "tracked actions" },
      { label: "Surface", value: "task-driven" },
    ],
    primaryActionLabel: "Open timeline view",
    secondaryActionLabel: "Review tracked items",
    detailCards: [
      {
        title: "Timeline discipline",
        body: "The final dashboard should feel like an execution lane, not a generic analytics board with decorative KPIs.",
      },
      {
        title: "Status clarity",
        body: "Application updates should be visible and legible without depending on color alone.",
      },
    ],
    placeholderList: [
      "deadline timeline",
      "tracked scholarship states",
      "document and next-step modules",
    ],
  },
  "document-feedback": {
    eyebrow: "Writing support",
    title: "Document feedback route scaffold",
    summary:
      "This route reserves the bounded SOP feedback experience documented for MVP, without expanding into a general writing suite.",
    metrics: [
      { label: "Scope", value: "SOP feedback" },
      { label: "AI role", value: "advisory" },
      { label: "Fallback", value: "required" },
    ],
    primaryActionLabel: "Analyze current draft",
    secondaryActionLabel: "Use fallback guidance",
    detailCards: [
      {
        title: "Draft-first flow",
        body: "The eventual screen should keep draft input and feedback in one intentional rhythm rather than splitting attention across many tools.",
      },
      {
        title: "Authority boundary",
        body: "Scholarship rules remain a structured data concern and should not be delegated to generated assistance copy.",
      },
    ],
    placeholderList: [
      "draft input region",
      "feedback and revision region",
      "error, loading, and saved states",
    ],
  },
  "interview-practice": {
    eyebrow: "Practice flow",
    title: "Interview practice route scaffold",
    summary:
      "This route reserves the text-first interview session flow for prompt, answer, and rubric-based readiness feedback.",
    metrics: [
      { label: "Input", value: "text-first" },
      { label: "Feedback", value: "rubric-based" },
      { label: "Promise", value: "non-predictive" },
    ],
    primaryActionLabel: "Start practice session",
    secondaryActionLabel: "Resume prior session",
    detailCards: [
      {
        title: "One prompt at a time",
        body: "The final route should avoid noisy multi-panel layouts and keep the active question visually dominant.",
      },
      {
        title: "Readiness framing",
        body: "Language should stay grounded in practice quality and improvement guidance rather than outcome prediction.",
      },
    ],
    placeholderList: [
      "session setup",
      "active question and answer region",
      "per-answer and session summary feedback",
    ],
  },
};
