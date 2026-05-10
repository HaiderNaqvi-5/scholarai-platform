"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth/AuthProvider";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}

function LoginInner() {
  const auth = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/feed";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (auth.status === "authed") router.replace(next);
  }, [auth.status, next, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await auth.login({ email, password });
      router.replace(next);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't sign you in.";
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
        <h1 className="mt-6 font-display text-2xl text-ink">Sign in</h1>
        <p className="mt-1 text-sm text-ink-muted">Pick up where you left off.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error ? (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          ) : null}
          <Button type="submit" loading={submitting} className="w-full" size="lg">
            Sign in
          </Button>
        </form>

        <p className="mt-6 text-sm text-ink-muted">
          New here?{" "}
          <Link href="/signup" className="text-generated underline-offset-2 hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
