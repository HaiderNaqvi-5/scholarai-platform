"use client";

/**
 * /onboarding — 4-step Pakistan profile (Front-upgrade §6.7 — abridged
 * to the 4 steps the backend currently consumes; the §6.7 5-step layout
 * splits Academic + Tests; harmless to ship as 4 until that backend split
 * lands).
 *
 * Save-as-you-go via PATCH on each step (handled by the final submit
 * here for now). "Saved" chip appears once per step transition.
 *
 * Per-screen bans: "Almost there! 🚀", floating mascot, "AI is analyzing
 * your profile", auto-skip on speed-fill.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Chip as UiChip } from "@/components/ui/badge";
import { endpoints } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "grantpath.onboarding_draft";

const FIELD_TAGS = [
  "Data Science",
  "AI / Machine Learning",
  "Analytics",
  "Computer Science",
  "Statistics",
  "Other",
];

const COUNTRIES = [
  { code: "PK", label: "Pakistan" },
  { code: "IN", label: "India" },
  { code: "BD", label: "Bangladesh" },
  { code: "NG", label: "Nigeria" },
  { code: "EG", label: "Egypt" },
  { code: "OTHER", label: "Other" },
];

const TARGET_COUNTRIES = [
  { code: "GB", label: "United Kingdom" },
  { code: "US", label: "United States" },
  { code: "CA", label: "Canada" },
  { code: "DE", label: "Germany" },
  { code: "AU", label: "Australia" },
];

type Draft = {
  full_name: string;
  citizenship: string;
  target_country: string;
  language_score: string;
  language_test: "IELTS" | "TOEFL" | "PTE" | "NONE";
  gpa: string;
  gpa_scale: string;
  degree_level: "BS" | "MS" | "PHD";
  field_tags: string[];
};

const STEPS = [
  { h1: "About you.", helper: "Your name appears on the documents you draft." },
  { h1: "Your academic record.", helper: "We support 4.0, 5.0, first-class, and percentage scales." },
  { h1: "Your test scores.", helper: "Skip if you haven't tested yet — we'll match without scores." },
  { h1: "Your goal.", helper: "Target country and field steer every match." },
] as const;

export default function OnboardingPage() {
  const router = useRouter();
  const auth = useAuth();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [savedChip, setSavedChip] = useState(false);
  const [draft, setDraft] = useState<Draft>({
    full_name: "",
    citizenship: "PK",
    target_country: "GB",
    language_score: "",
    language_test: "IELTS",
    gpa: "",
    gpa_scale: "4.0",
    degree_level: "MS",
    field_tags: ["Data Science"],
  });

  useEffect(() => {
    if (auth.status === "guest") router.replace("/login?next=/onboarding");
    if (auth.status === "authed" && !draft.full_name) {
      /* eslint-disable-next-line react-hooks/set-state-in-effect */
      setDraft((d) => ({ ...d, full_name: auth.user.full_name || "" }));
    }
  }, [auth.status, auth, router, draft.full_name]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      /* eslint-disable-next-line react-hooks/set-state-in-effect */
      if (raw) setDraft((d) => ({ ...d, ...JSON.parse(raw) }));
    } catch {}
  }, []);

  useEffect(() => {
    const id = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
      } catch {}
    }, 200);
    return () => clearTimeout(id);
  }, [draft]);

  const update = <K extends keyof Draft>(k: K, v: Draft[K]) =>
    setDraft((d) => ({ ...d, [k]: v }));

  const canAdvance = () => {
    if (step === 0) return draft.full_name.trim().length > 1;
    if (step === 1) return true;
    if (step === 2) return draft.citizenship.length > 0;
    if (step === 3) return draft.field_tags.length > 0 && !!draft.degree_level;
    return false;
  };

  function next() {
    setSavedChip(true);
    setTimeout(() => setSavedChip(false), 1_500);
    setStep((s) => s + 1);
  }

  async function submit() {
    setSubmitting(true);
    try {
      const cc = draft.citizenship === "OTHER" ? "ZZ" : draft.citizenship;
      await endpoints.profile.upsert({
        citizenship_country_code: cc,
        gpa_value: draft.gpa ? Number(draft.gpa) : null,
        gpa_scale: draft.gpa_scale ? Number(draft.gpa_scale) : 4.0,
        target_field: draft.field_tags.join(", ") || "Data Science",
        target_degree_level: draft.degree_level,
        target_country_code: draft.target_country,
        language_test_type: draft.language_test !== "NONE" ? draft.language_test : null,
        language_test_score:
          draft.language_test !== "NONE" && draft.language_score
            ? Number(draft.language_score)
            : null,
      });
      localStorage.removeItem(STORAGE_KEY);
      toast.success("Profile saved.");
      router.replace("/dashboard/scholarships/match");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Couldn't save profile. Try again.";
      toast.error(msg);
      setSubmitting(false);
    }
  }

  const current = STEPS[step];

  return (
    <div className="min-h-screen bg-ivory">
      <header className="border-b border-[var(--color-border-quiet)]">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4 md:px-12">
          <span className="font-display text-[22px] italic font-[450] tracking-[-0.02em] text-ink-deep">
            AidwiseAI
          </span>
          {savedChip ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-validated-soft px-2.5 py-1 text-[11px] font-mono uppercase tracking-[0.06em] text-validated">
              <Check className="size-3" strokeWidth={2} /> Saved
            </span>
          ) : null}
        </div>
      </header>

      <main id="main" className="mx-auto flex w-full max-w-[560px] flex-col px-6 py-10 md:py-16">
        {/* Progress */}
        <nav aria-label="Onboarding steps" className="mb-8">
          <div className="flex items-center gap-1.5">
            {STEPS.map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1 flex-1 rounded-full transition-colors duration-[var(--motion-layout)]",
                  i < step
                    ? "bg-lapis"
                    : i === step
                      ? "bg-lapis"
                      : "bg-paper-edge",
                )}
              />
            ))}
          </div>
          <p className="mt-3 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            Step {step + 1} of {STEPS.length}
          </p>
        </nav>

        <h1 className="font-display text-[32px] italic font-[400] leading-[1.15] tracking-[-0.02em] text-ink-deep md:text-[36px]">
          {current.h1}
        </h1>
        <p className="mt-2 text-[14px] leading-[1.55] text-ink-muted">{current.helper}</p>

        <div key={step} className="fade-up mt-8 flex-1 space-y-5">
          {step === 0 && (
            <Field label="Your name" htmlFor="full_name">
              <Input
                id="full_name"
                value={draft.full_name}
                onChange={(e) => update("full_name", e.target.value)}
                autoFocus
                autoComplete="name"
                placeholder="Aisha Khan"
              />
            </Field>
          )}

          {step === 1 && (
            <Field label="GPA" htmlFor="gpa" helper="If your GPA is 3.4 / 4.0, type 3.4 and pick 4.0.">
              <div className="flex flex-wrap items-center gap-2">
                <Input
                  id="gpa"
                  value={draft.gpa}
                  inputMode="decimal"
                  placeholder="3.6"
                  onChange={(e) => update("gpa", e.target.value)}
                  className="max-w-[140px]"
                />
                <span className="text-[14px] text-ink-muted">on a</span>
                <select
                  value={draft.gpa_scale}
                  onChange={(e) => update("gpa_scale", e.target.value)}
                  className="h-11 rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 text-[14px] text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
                >
                  <option value="4.0">4.0 scale</option>
                  <option value="5.0">5.0 scale</option>
                  <option value="10.0">10 scale</option>
                  <option value="100">100 scale</option>
                </select>
              </div>
            </Field>
          )}

          {step === 2 && (
            <>
              <Field label="Where are you a citizen?" htmlFor="citizenship">
                <select
                  id="citizenship"
                  value={draft.citizenship}
                  onChange={(e) => update("citizenship", e.target.value)}
                  className="h-11 w-full rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 text-[14px] text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="English test" htmlFor="lang_test">
                <div className="flex flex-wrap items-center gap-2">
                  <select
                    id="lang_test"
                    value={draft.language_test}
                    onChange={(e) =>
                      update("language_test", e.target.value as Draft["language_test"])
                    }
                    className="h-11 rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 text-[14px] text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
                  >
                    <option value="IELTS">IELTS</option>
                    <option value="TOEFL">TOEFL</option>
                    <option value="PTE">PTE</option>
                    <option value="NONE">Haven&apos;t taken</option>
                  </select>
                  {draft.language_test !== "NONE" ? (
                    <Input
                      value={draft.language_score}
                      inputMode="decimal"
                      placeholder="Score"
                      onChange={(e) => update("language_score", e.target.value)}
                      className="max-w-[140px]"
                    />
                  ) : null}
                </div>
              </Field>
            </>
          )}

          {step === 3 && (
            <>
              <Field label="Where do you want to study?" htmlFor="target_country">
                <select
                  id="target_country"
                  value={draft.target_country}
                  onChange={(e) => update("target_country", e.target.value)}
                  className="h-11 w-full rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 text-[14px] text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
                >
                  {TARGET_COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Which degree are you applying for?">
                <div className="flex flex-wrap gap-2">
                  {(["BS", "MS", "PHD"] as const).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => update("degree_level", d)}
                      className={cn(
                        "h-10 rounded-[10px] px-4 font-medium text-[13px] transition-colors duration-[var(--motion-micro)]",
                        draft.degree_level === d
                          ? "bg-lapis text-paper-white"
                          : "border border-[var(--color-border)] bg-paper-white text-ink-deep hover:bg-paper-warm",
                      )}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </Field>

              <Field label="What field?" helper="Pick one or more.">
                <div className="flex flex-wrap gap-2">
                  {FIELD_TAGS.map((t) => {
                    const active = draft.field_tags.includes(t);
                    return (
                      <button
                        key={t}
                        type="button"
                        onClick={() =>
                          update(
                            "field_tags",
                            active
                              ? draft.field_tags.filter((x) => x !== t)
                              : [...draft.field_tags, t],
                          )
                        }
                        className={cn(
                          "h-10 rounded-[10px] px-4 text-[13px] transition-colors duration-[var(--motion-micro)] tap-target",
                          active
                            ? "bg-lapis text-paper-white"
                            : "border border-[var(--color-border)] bg-paper-white text-ink-deep hover:bg-paper-warm",
                        )}
                      >
                        {t}
                      </button>
                    );
                  })}
                </div>
              </Field>
            </>
          )}
        </div>

        <footer className="mt-12 flex items-center justify-between gap-3 border-t border-[var(--color-border-quiet)] pt-6">
          {step > 0 ? (
            <Button variant="ghost" onClick={() => setStep((s) => s - 1)}>
              <ArrowLeft className="size-4" strokeWidth={1.5} />
              Back
            </Button>
          ) : (
            <span />
          )}
          {step < STEPS.length - 1 ? (
            <Button onClick={next} disabled={!canAdvance()}>
              Continue <ArrowRight className="size-4" strokeWidth={1.5} />
            </Button>
          ) : (
            <Button onClick={submit} loading={submitting} disabled={!canAdvance()} size="lg">
              Show my matches <ArrowRight className="size-4" strokeWidth={1.5} />
            </Button>
          )}
        </footer>
      </main>
    </div>
  );
}

function Field({
  label,
  helper,
  htmlFor,
  children,
}: {
  label: string;
  helper?: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Label htmlFor={htmlFor} className="block text-[13px] font-medium text-ink-deep">
        {label}
      </Label>
      {helper ? (
        <p className="mt-1 text-[12px] leading-[1.5] text-ink-subtle">{helper}</p>
      ) : null}
      <div className="mt-2">{children}</div>
    </div>
  );
}
// UiChip imported but the new step UI uses native buttons for hover/active control — keeping the import for parity with the shared chip atom.
void UiChip;
