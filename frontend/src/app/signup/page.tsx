"use client";

/**
 * /signup — Registration (Front-upgrade §6.5).
 *
 * Split layout (md+): editorial copy left, form right. On 375 the
 * editorial copy collapses and the form takes the full bleed.
 * Invite-code variants (`?invite=AIRU2026`) reveal the Air University
 * cohort fields and pin the invite chip above the email input.
 *
 * Per-screen bans: confetti on submit, "Excellent! 🔥" password rating,
 * faux-social signup buttons, gray-on-gray legal microcopy.
 */

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { toast } from "sonner";
import { Eye, EyeOff, X, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth/AuthProvider";
import { ApiError } from "@/lib/api";
import { BRAND_DISPLAY_NAME } from "@/lib/brand";
import { cn } from "@/lib/utils";

const AIR_UNI_INVITE = "AIRU2026";

function passwordScore(pw: string): { score: 0 | 1 | 2 | 3; label: string } {
  if (pw.length < 12) return { score: 0, label: "Too short" };
  const hasMixed = /[a-z]/.test(pw) && /[A-Z]/.test(pw);
  const hasDigit = /\d/.test(pw);
  const long = pw.length >= 16;
  const points = (hasMixed ? 1 : 0) + (hasDigit ? 1 : 0) + (long ? 1 : 0);
  if (points <= 1) return { score: 1, label: "Weak" };
  if (points === 2) return { score: 2, label: "OK" };
  return { score: 3, label: "Strong" };
}

export default function SignupPage() {
  return (
    <Suspense fallback={null}>
      <SignupInner />
    </Suspense>
  );
}

function SignupInner() {
  const auth = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const initialInvite = params.get("invite") || "";

  const [invite, setInvite] = useState(initialInvite);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [pdpb, setPdpb] = useState(false);
  const [marketing, setMarketing] = useState(false);
  /* Air U cohort fields — only shown when invite=AIRU2026 */
  const [airUni, setAirUni] = useState("Air University");
  const [airDept, setAirDept] = useState("");
  const [airBatch, setAirBatch] = useState("");
  const [fullName, setFullName] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isAirU = invite.toUpperCase() === AIR_UNI_INVITE;
  const meter = useMemo(() => passwordScore(password), [password]);
  const canSubmit = email.length > 3 && meter.score >= 1 && pdpb;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await auth.signup({
        email,
        password,
        full_name: fullName || undefined,
        // Other fields require backend wiring; harmless if ignored.
        ...(invite ? { invite_code: invite } : {}),
        ...(isAirU
          ? { air_uni_uni: airUni, air_uni_dept: airDept, air_uni_batch: airBatch }
          : {}),
        marketing_opt_in: marketing,
        consent_v: "1.0",
      } as Parameters<typeof auth.signup>[0]);
      router.replace("/onboarding");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't create your account.";
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-ivory">
      {/* Mini LandingNav per §6.5 anatomy */}
      <header className="border-b border-[var(--color-border-quiet)]">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4 md:px-12">
          <Link
            href="/"
            className="font-display text-[22px] italic font-[450] tracking-[-0.02em] text-ink-deep"
          >
            {BRAND_DISPLAY_NAME}
          </Link>
          <Link href="/login" className="text-[13px] text-ink-muted hover:text-ink-deep">
            Sign in
          </Link>
        </div>
      </header>

      <main id="main" className="mx-auto grid max-w-[1200px] gap-12 px-6 py-12 md:grid-cols-12 md:gap-16 md:px-12 md:py-20">
        {/* Editorial copy (md+) */}
        <section className="hidden md:col-span-5 md:block">
          <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-ink-subtle">
            Step 1 of 2
          </p>
          <h1 className="mt-4 font-display text-[48px] italic font-[400] leading-[1.05] tracking-[-0.02em] text-ink-deep">
            Two minutes.
            <br />
            Then matches.
          </h1>
          <p className="mt-5 max-w-[34ch] text-[16px] leading-[1.55] text-ink-muted">
            Set up your {BRAND_DISPLAY_NAME} account. We match you against live
            scholarships immediately after onboarding — no consultant call.
          </p>
          <ul className="mt-10 space-y-4 text-[14px] text-ink-muted">
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
              <span>PDPB-aligned. We never sell or share your data without consent.</span>
            </li>
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
              <span>Pakistan-priced. PKR 0 to start. No card on file.</span>
            </li>
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
              <span>Cancel anytime — even mid-trial — with one click in settings.</span>
            </li>
          </ul>
        </section>

        {/* Form (full bleed on 375) */}
        <section className="md:col-span-7">
          <h1 className="font-display text-[28px] italic font-[400] leading-tight tracking-[-0.02em] text-ink-deep md:hidden">
            Create your account
          </h1>

          {invite ? (
            <div className="mb-6 flex items-center justify-between gap-3 rounded-[12px] border border-gold-leaf/30 bg-gold-soft px-4 py-3">
              <div className="flex items-center gap-3">
                <Badge tone="gold">Invite</Badge>
                <p className="text-[13px] text-ink-deep">
                  Using code{" "}
                  <span className="font-mono font-semibold tracking-[0.06em]">{invite}</span>
                  {isAirU ? " — 30-day Pro trial" : ""}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setInvite("")}
                aria-label="Remove invite code"
                className="text-ink-muted hover:text-ink-deep"
              >
                <X className="size-4" strokeWidth={1.5} />
              </button>
            </div>
          ) : null}

          <form onSubmit={onSubmit} className="space-y-5" noValidate>
            <Field id="signup-name" label="Your name" optional>
              <Input
                id="signup-name"
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </Field>

            <Field id="signup-email" label="Email" required>
              <Input
                id="signup-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>

            <div>
              <Label htmlFor="signup-password" className="mb-1.5 block text-[13px] font-medium text-ink-deep">
                Password{" "}
                <span className="font-mono text-[11px] font-normal uppercase tracking-[0.06em] text-ink-subtle">
                  (12 characters minimum)
                </span>
              </Label>
              <div className="relative">
                <Input
                  id="signup-password"
                  type={showPw ? "text" : "password"}
                  autoComplete="new-password"
                  minLength={12}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pr-12"
                  aria-describedby="signup-password-meter"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-deep"
                >
                  {showPw ? <EyeOff className="size-4" strokeWidth={1.5} /> : <Eye className="size-4" strokeWidth={1.5} />}
                </button>
              </div>
              <PasswordMeter score={meter.score} label={meter.label} id="signup-password-meter" />
            </div>

            {isAirU ? (
              <fieldset className="grid gap-4 rounded-[12px] border border-[var(--color-border)] bg-paper-warm/40 p-4 md:grid-cols-3">
                <legend className="px-1 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                  Air University cohort
                </legend>
                <Field id="air-uni" label="University">
                  <Input id="air-uni" value={airUni} onChange={(e) => setAirUni(e.target.value)} />
                </Field>
                <Field id="air-dept" label="Department">
                  <Input
                    id="air-dept"
                    placeholder="e.g. Computer Science"
                    value={airDept}
                    onChange={(e) => setAirDept(e.target.value)}
                  />
                </Field>
                <Field id="air-batch" label="Batch year">
                  <Input
                    id="air-batch"
                    inputMode="numeric"
                    placeholder="2026"
                    value={airBatch}
                    onChange={(e) => setAirBatch(e.target.value)}
                  />
                </Field>
              </fieldset>
            ) : null}

            <Checkbox
              id="pdpb"
              checked={pdpb}
              onChange={setPdpb}
              required
              label={
                <>
                  I have read and agree to the{" "}
                  <Link href="/legal/privacy" className="text-lapis underline underline-offset-2">
                    Privacy Notice (v1.0)
                  </Link>
                  .
                </>
              }
              helper="Required. We log a hash of the document you agreed to."
            />

            <Checkbox
              id="marketing"
              checked={marketing}
              onChange={setMarketing}
              label="Email me when scholarships matching my profile open. Unsubscribe anytime."
            />

            {error ? (
              <p role="alert" className="rounded-[10px] border border-sindoor/30 bg-sindoor-soft px-3 py-2 text-[13px] text-sindoor">
                {error}
              </p>
            ) : null}

            <Button
              type="submit"
              loading={submitting}
              disabled={!canSubmit}
              className="w-full"
              size="lg"
            >
              Create account
            </Button>

            <p className="text-center text-[13px] text-ink-muted">
              Already have an account?{" "}
              <Link href="/login" className="text-lapis underline underline-offset-2 hover:decoration-2">
                Sign in
              </Link>
            </p>
          </form>
        </section>
      </main>
    </div>
  );
}

function Field({
  id,
  label,
  required,
  optional,
  children,
}: {
  id: string;
  label: string;
  required?: boolean;
  optional?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Label htmlFor={id} className="mb-1.5 block text-[13px] font-medium text-ink-deep">
        {label}{" "}
        {required ? (
          <span aria-hidden className="text-sindoor">*</span>
        ) : optional ? (
          <span className="font-mono text-[11px] font-normal uppercase tracking-[0.06em] text-ink-subtle">
            (optional)
          </span>
        ) : null}
      </Label>
      {children}
    </div>
  );
}

function Checkbox({
  id,
  checked,
  onChange,
  label,
  helper,
  required,
}: {
  id: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  label: React.ReactNode;
  helper?: string;
  required?: boolean;
}) {
  return (
    <label
      htmlFor={id}
      className="flex cursor-pointer items-start gap-3 rounded-[10px] border border-transparent px-1 py-2 transition-colors hover:bg-paper-warm/40"
    >
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        required={required}
        className="mt-0.5 size-[18px] cursor-pointer rounded-[4px] border border-[var(--color-border)] accent-lapis"
      />
      <span className="flex-1 text-[13px] leading-[1.55] text-ink-deep">
        {label}
        {helper ? <span className="mt-0.5 block text-[11px] text-ink-subtle">{helper}</span> : null}
      </span>
    </label>
  );
}

function PasswordMeter({ score, label, id }: { score: 0 | 1 | 2 | 3; label: string; id: string }) {
  const tone =
    score === 0
      ? "text-ink-subtle"
      : score === 1
        ? "text-sindoor"
        : score === 2
          ? "text-caution"
          : "text-validated";
  return (
    <div className="mt-2" id={id} aria-live="polite">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={cn(
              "h-1 flex-1 rounded-full transition-colors duration-[var(--motion-micro)]",
              i < score
                ? score === 1
                  ? "bg-sindoor"
                  : score === 2
                    ? "bg-caution"
                    : "bg-validated"
                : "bg-paper-edge",
            )}
          />
        ))}
      </div>
      <p className={cn("mt-1.5 font-mono text-[11px] uppercase tracking-[0.06em]", tone)}>{label}</p>
    </div>
  );
}
