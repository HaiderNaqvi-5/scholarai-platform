"use client";

/**
 * /signup — Registration (Front-upgrade §6.5).
 *
 * Split layout (md+): editorial copy left, form right. On 375 the
 * editorial copy collapses and the form takes the full bleed.
 * Invite-code chip surfaces above the email input when `?invite=<code>`
 * is present in the query string.
 *
 * Dual-mode: when NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is set, signup runs
 * through Clerk (`useClerkSignupFlow`) with a 2nd-step email-code panel
 * rendered inside the same <section>. Local mode posts to the legacy
 * backend `/auth/register` (gated to 410 when backend AUTH_PROVIDER=clerk).
 *
 * Per-screen bans: confetti on submit, "Excellent! 🔥" password rating,
 * faux-social signup buttons, gray-on-gray legal microcopy.
 */

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
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
import { clerkEnabled, useClerkSignupFlow } from "@/lib/auth/clerkAdapter";
import { SocialAuthButtons } from "@/components/auth/SocialAuthButtons";

const PASSWORD_SPECIAL_RE = /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/;

function passwordScore(pw: string): { score: 0 | 1 | 2 | 3; label: string } {
  if (pw.length < 12) return { score: 0, label: "Too short" };
  const hasLower = /[a-z]/.test(pw);
  const hasUpper = /[A-Z]/.test(pw);
  const hasDigit = /\d/.test(pw);
  const hasSpecial = PASSWORD_SPECIAL_RE.test(pw);
  const passed = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length;
  if (passed <= 1) return { score: 1, label: "Weak" };
  if (passed <= 3) return { score: 2, label: "Add a symbol, upper, lower, and number" };
  return { score: 3, label: "Strong" };
}

function isBackendValidPassword(pw: string): boolean {
  return (
    pw.length >= 12 &&
    /[a-z]/.test(pw) &&
    /[A-Z]/.test(pw) &&
    /\d/.test(pw) &&
    PASSWORD_SPECIAL_RE.test(pw)
  );
}

type CreateSubmit = (input: {
  email: string;
  password: string;
  fullName: string;
  invite: string;
  marketing: boolean;
  pdpb: boolean;
}) => Promise<void>;

type VerifySubmit = (code: string) => Promise<void>;

type ResendFn = () => Promise<void>;

export default function SignupPage() {
  return (
    <Suspense fallback={null}>
      {clerkEnabled ? <ClerkSignupInner /> : <LocalSignupInner />}
    </Suspense>
  );
}

function ClerkSignupInner() {
  const router = useRouter();
  const flow = useClerkSignupFlow();
  const create: CreateSubmit = async (input) => {
    await flow.create({
      email: input.email,
      password: input.password,
      fullName: input.fullName,
    });
    if (input.marketing || input.pdpb || input.invite) {
      // PDPB consent + invite cohort fields are not persisted yet — backend
      // route POST /profile/onboarding-prefs is deferred. UI collected them
      // so the flow shape stays identical to local mode.
      console.warn(
        "[clerk-signup] onboarding prefs not persisted in clerk mode — TODO POST /profile/onboarding-prefs",
        { invite: input.invite, marketing: input.marketing, pdpb: input.pdpb },
      );
    }
  };
  const verify: VerifySubmit = async (code) => {
    await flow.verifyCode(code);
    router.replace("/onboarding");
  };
  const resend: ResendFn = async () => {
    await flow.resend();
  };
  return <SignupInner create={create} verify={verify} resend={resend} requireEmailCode />;
}

function LocalSignupInner() {
  const router = useRouter();
  const auth = useAuth();
  const create: CreateSubmit = async (input) => {
    await auth.signup({
      email: input.email,
      password: input.password,
      full_name: input.fullName.trim(),
      ...(input.invite ? { invite_code: input.invite } : {}),
      marketing_consent: input.marketing,
      terms_version: "1.0",
      privacy_version: "1.0",
      accepted: input.pdpb,
    });
    router.replace("/onboarding");
  };
  // Local mode never enters the verify step.
  const verify: VerifySubmit = async () => undefined;
  const resend: ResendFn = async () => undefined;
  return <SignupInner create={create} verify={verify} resend={resend} requireEmailCode={false} />;
}

function SignupInner({
  create,
  verify,
  resend,
  requireEmailCode,
}: {
  create: CreateSubmit;
  verify: VerifySubmit;
  resend: ResendFn;
  requireEmailCode: boolean;
}) {
  const params = useSearchParams();
  const initialInvite = params.get("invite") || "";

  const [step, setStep] = useState<"create" | "verify">("create");
  const [invite, setInvite] = useState(initialInvite);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [pdpb, setPdpb] = useState(false);
  const [marketing, setMarketing] = useState(false);
  const [fullName, setFullName] = useState("");

  const [code, setCode] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const meter = useMemo(() => passwordScore(password), [password]);
  const canSubmit =
    email.length > 3 && fullName.trim().length >= 2 && isBackendValidPassword(password) && pdpb;

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setInterval(() => setResendCooldown((s) => Math.max(0, s - 1)), 1_000);
    return () => clearInterval(t);
  }, [resendCooldown]);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await create({ email, password, fullName, invite, marketing, pdpb });
      if (requireEmailCode) {
        setStep("verify");
        setResendCooldown(30);
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't create your account.";
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  async function onVerify() {
    if (code.length !== 6) return;
    setSubmitting(true);
    setError(null);
    try {
      await verify(code);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't verify the code.";
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  async function onResend() {
    if (resendCooldown > 0) return;
    setError(null);
    try {
      await resend();
      setResendCooldown(30);
      toast.success("Code resent.");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't resend the code.";
      setError(msg);
      toast.error(msg);
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
            Step {step === "create" ? "1" : "2"} of 2
          </p>
          <h1 className="mt-4 font-display text-[48px] italic font-[400] leading-[1.05] tracking-[-0.02em] text-ink-deep">
            {step === "create" ? (
              <>Two minutes.<br />Then matches.</>
            ) : (
              <>Verify your<br />email.</>
            )}
          </h1>
          <p className="mt-5 max-w-[34ch] text-[16px] leading-[1.55] text-ink-muted">
            {step === "create"
              ? `Set up your ${BRAND_DISPLAY_NAME} account. We match you against live scholarships immediately after onboarding — no consultant call.`
              : `We sent a 6-digit code to confirm your email. It usually arrives in under a minute.`}
          </p>
          {step === "create" && (
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
          )}
        </section>

        {/* Form (full bleed on 375) */}
        <section className="md:col-span-7">
          <h1 className="font-display text-[28px] italic font-[400] leading-tight tracking-[-0.02em] text-ink-deep md:hidden">
            {step === "create" ? "Create your account" : "Verify your email"}
          </h1>

          {step === "create" && invite ? (
            <div className="mb-6 flex items-center justify-between gap-3 rounded-[12px] border border-gold-leaf/30 bg-gold-soft px-4 py-3">
              <div className="flex items-center gap-3">
                <Badge tone="gold">Invite</Badge>
                <p className="text-[13px] text-ink-deep">
                  Using code{" "}
                  <span className="font-mono font-semibold tracking-[0.06em]">{invite}</span>
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

          {step === "create" && clerkEnabled ? (
            <div className="mb-6">
              <SocialAuthButtons mode="signup" />
            </div>
          ) : null}

          {step === "create" ? (
            <form onSubmit={onCreate} className="space-y-5" noValidate>
              <Field id="signup-name" label="Your name" required>
                <Input
                  id="signup-name"
                  autoComplete="name"
                  required
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
                    (12+ chars, upper/lower, number, symbol)
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
                {requireEmailCode ? "Continue" : "Create account"}
              </Button>

              <p className="text-center text-[13px] text-ink-muted">
                Already have an account?{" "}
                <Link href="/login" className="text-lapis underline underline-offset-2 hover:decoration-2">
                  Sign in
                </Link>
              </p>
            </form>
          ) : (
            <div className="space-y-5 transition-opacity duration-200 ease-out">
              <p className="text-[13px] text-ink-muted">
                We sent a 6-digit code to{" "}
                <span className="font-medium text-ink-deep">{email}</span>.
              </p>
              <Field id="signup-code" label="Verification code" required>
                <Input
                  id="signup-code"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  autoComplete="one-time-code"
                  autoFocus
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                />
              </Field>
              {error ? (
                <p role="alert" className="rounded-[10px] border border-sindoor/30 bg-sindoor-soft px-3 py-2 text-[13px] text-sindoor">
                  {error}
                </p>
              ) : null}
              <Button
                type="button"
                onClick={onVerify}
                loading={submitting}
                disabled={code.length !== 6}
                className="w-full"
                size="lg"
              >
                Verify and continue
              </Button>
              <button
                type="button"
                onClick={onResend}
                disabled={resendCooldown > 0}
                className="block w-full text-center text-[13px] text-lapis underline underline-offset-2 disabled:text-ink-subtle disabled:no-underline"
              >
                {resendCooldown > 0 ? `Resend code in ${resendCooldown}s` : "Resend code"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setStep("create");
                  setCode("");
                  setError(null);
                }}
                className="block w-full text-center text-[12px] text-ink-muted hover:text-ink-deep"
              >
                Use a different email
              </button>
            </div>
          )}
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
