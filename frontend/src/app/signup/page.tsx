"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth/AuthProvider";
import { ApiError } from "@/lib/api";

export default function SignupPage() {
  const auth = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await auth.signup({ email, password, full_name: fullName || undefined });
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
    <div className="flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm">
        <Link href="/" className="font-display text-lg text-ink">GrantPath</Link>
        <h1 className="mt-6 font-display text-2xl text-ink">Create your account</h1>
        <p className="mt-1 text-sm text-ink-muted">Two minutes. No credit card.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="fullName">Your name</Label>
            <Input
              id="fullName"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <p className="text-xs text-ink-subtle">Minimum 8 characters.</p>
          </div>
          {error ? (
            <p role="alert" className="text-sm text-danger">{error}</p>
          ) : null}
          <Button type="submit" loading={submitting} className="w-full" size="lg">
            Create account
          </Button>
        </form>

        <p className="mt-6 text-sm text-ink-muted">
          Have an account?{" "}
          <Link href="/login" className="text-generated underline-offset-2 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
