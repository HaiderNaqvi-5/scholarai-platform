"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

const STEPS = ["You", "Academic", "Citizenship & language", "Goal"] as const;

export default function OnboardingPage() {
  const router = useRouter();
  const auth = useAuth();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
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
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDraft((d) => ({ ...d, full_name: auth.user.full_name || "" }));
    }
  }, [auth.status, auth, router, draft.full_name]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
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
        language_test_type:
          draft.language_test !== "NONE" ? draft.language_test : null,
        language_test_score:
          draft.language_test !== "NONE" && draft.language_score
            ? Number(draft.language_score)
            : null,
      });
      localStorage.removeItem(STORAGE_KEY);
      toast.success("Profile saved.");
      router.replace("/feed");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Couldn't save profile. Try again.";
      toast.error(msg);
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-xl flex-col px-5 py-10">
      <header className="mb-8">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-ink-subtle">
          Step {step + 1} of {STEPS.length}
        </p>
        <h1 className="mt-2 font-display text-3xl text-ink">{STEPS[step]}</h1>
        <ProgressDots count={STEPS.length} active={step} />
      </header>

      <div className="flex-1 space-y-5">
        {step === 0 && (
          <Field label="What should we call you?" htmlFor="full_name" hint="Used on documents you submit.">
            <Input
              id="full_name"
              value={draft.full_name}
              onChange={(e) => update("full_name", e.target.value)}
              autoFocus
              autoComplete="name"
            />
          </Field>
        )}

        {step === 1 && (
          <>
            <Field label="GPA (optional)" htmlFor="gpa" hint="Skip if you'd rather not say.">
              <div className="flex items-center gap-2">
                <Input
                  id="gpa"
                  value={draft.gpa}
                  inputMode="decimal"
                  placeholder="3.6"
                  onChange={(e) => update("gpa", e.target.value)}
                  className="max-w-[140px]"
                />
                <span className="text-ink-muted">on a</span>
                <select
                  value={draft.gpa_scale}
                  onChange={(e) => update("gpa_scale", e.target.value)}
                  className="h-11 rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
                >
                  <option value="4.0">4.0 scale</option>
                  <option value="5.0">5.0 scale</option>
                  <option value="10.0">10 scale</option>
                  <option value="100">100 scale</option>
                </select>
              </div>
            </Field>
          </>
        )}

        {step === 2 && (
          <>
            <Field label="Where are you a citizen?" htmlFor="citizenship" hint="Required — eligibility runs on this.">
              <select
                id="citizenship"
                value={draft.citizenship}
                onChange={(e) => update("citizenship", e.target.value)}
                className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
              >
                <option value="">Pick one</option>
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.label}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="English test (optional)" htmlFor="lang_test" hint="Skip if you haven't tested yet.">
              <div className="flex items-center gap-2">
                <select
                  id="lang_test"
                  value={draft.language_test}
                  onChange={(e) => update("language_test", e.target.value as Draft["language_test"])}
                  className="h-11 rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
                >
                  <option value="IELTS">IELTS</option>
                  <option value="TOEFL">TOEFL</option>
                  <option value="PTE">PTE</option>
                  <option value="NONE">None yet</option>
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
            <Field label="Where do you want to study?" htmlFor="target_country" hint="Required — funded programs in this country.">
              <select
                id="target_country"
                value={draft.target_country}
                onChange={(e) => update("target_country", e.target.value)}
                className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
              >
                {TARGET_COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.label}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Which degree are you applying for?" htmlFor="degree" hint="Required.">
              <div className="flex flex-wrap gap-2">
                {(["BS", "MS", "PHD"] as const).map((d) => (
                  <Chip
                    key={d}
                    active={draft.degree_level === d}
                    onClick={() => update("degree_level", d)}
                  >
                    {d}
                  </Chip>
                ))}
              </div>
            </Field>

            <Field label="What field?" hint="Pick one or more.">
              <div className="flex flex-wrap gap-2">
                {FIELD_TAGS.map((t) => {
                  const active = draft.field_tags.includes(t);
                  return (
                    <Chip
                      key={t}
                      active={active}
                      onClick={() =>
                        update(
                          "field_tags",
                          active
                            ? draft.field_tags.filter((x) => x !== t)
                            : [...draft.field_tags, t],
                        )
                      }
                    >
                      {t}
                    </Chip>
                  );
                })}
              </div>
            </Field>
          </>
        )}
      </div>

      <footer className="mt-10 flex items-center justify-between">
        {step > 0 ? (
          <Button variant="ghost" onClick={() => setStep((s) => s - 1)}>
            Back
          </Button>
        ) : (
          <span />
        )}
        {step < STEPS.length - 1 ? (
          <Button onClick={() => setStep((s) => s + 1)} disabled={!canAdvance()}>
            Continue <ArrowRight className="size-4" strokeWidth={2} />
          </Button>
        ) : (
          <Button onClick={submit} loading={submitting} disabled={!canAdvance()}>
            <Check className="size-4" strokeWidth={2} /> Save and see matches
          </Button>
        )}
      </footer>
    </div>
  );
}

function Field({
  label,
  hint,
  htmlFor,
  children,
}: {
  label: string;
  hint?: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor}>{label}</Label>
      {hint ? <p className="text-xs text-ink-subtle">{hint}</p> : null}
      {children}
    </div>
  );
}

function Chip({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "h-10 rounded-full px-4 text-sm transition-colors duration-150",
        active
          ? "bg-ink text-paper"
          : "border border-[var(--color-border)] bg-paper-white text-ink hover:bg-paper-warm",
      )}
    >
      {children}
    </button>
  );
}

function ProgressDots({ count, active }: { count: number; active: number }) {
  return (
    <div className="mt-4 flex gap-1.5" aria-hidden>
      {Array.from({ length: count }).map((_, i) => (
        <span
          key={i}
          className={cn(
            "h-1.5 rounded-full transition-all duration-200",
            i === active ? "w-8 bg-ink" : i < active ? "w-4 bg-ink-muted" : "w-4 bg-paper-dim",
          )}
        />
      ))}
    </div>
  );
}
