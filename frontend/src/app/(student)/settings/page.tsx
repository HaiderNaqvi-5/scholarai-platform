"use client";

import { useState } from "react";
import { LogOut, Mail, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth/AuthProvider";

export default function SettingsPage() {
  const auth = useAuth();
  const [signingOut, setSigningOut] = useState(false);

  if (auth.status !== "authed") {
    return null;
  }
  const user = auth.user;

  async function signOut() {
    setSigningOut(true);
    try {
      await auth.logout();
    } catch {
      toast.error("Couldn't sign out cleanly. Tokens cleared anyway.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="font-display text-3xl text-ink">Settings</h1>
        <p className="mt-1 text-ink-muted">Account, sessions, sign out.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Your sign-in identity.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-3">
          <Row icon={<Mail className="size-4" strokeWidth={2} />} label="Email" value={user.email} />
          <Row
            icon={<ShieldCheck className="size-4" strokeWidth={2} />}
            label="Role"
            value={<Badge tone="validated">{user.role}</Badge>}
          />
          {user.full_name ? (
            <Row icon={null} label="Name" value={user.full_name} />
          ) : null}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Email & password</CardTitle>
          <CardDescription>Change your sign-in credentials.</CardDescription>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-ink-subtle">
            Email and password changes are not available yet. Contact support if you need to update
            either.
          </p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
          <CardDescription>Sign out of GrantPath on this device.</CardDescription>
        </CardHeader>
        <CardBody>
          <Button variant="danger" onClick={signOut} loading={signingOut}>
            <LogOut className="size-4" strokeWidth={2} /> Sign out
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}

function Row({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[var(--color-border)] pb-3 last:border-b-0 last:pb-0">
      <div className="flex items-center gap-2 text-sm text-ink-muted">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-sm text-ink">{value}</div>
    </div>
  );
}
