"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/ui/section-header";
import { TypedConfirm } from "@/components/settings/TypedConfirm";
import { useAuth } from "@/lib/auth/AuthProvider";
import { endpoints } from "@/lib/api";
import { readConsent, writeConsent } from "@/components/consent/CookieBanner";
import type {
  ConsentState,
  DataDeletionRequestResponse,
  DataExportResponse,
} from "@/lib/api/types";

const PLAN_LABEL: Record<string, string> = {
  free: "Explorer",
  pro: "Pro",
  elite: "Elite",
  institution: "Institution",
  demo: "Demo",
};

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function SettingsPage() {
  const auth = useAuth();
  if (auth.status !== "authed") return null;
  return <SettingsBody />;
}

function SettingsBody() {
  return (
    <div className="mx-auto max-w-[820px]" data-testid="settings-tabs">
      <PageHeader title="Settings" />
      <Tabs defaultValue="account" className="mt-6">
        <TabsList className="flex flex-wrap">
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="privacy">Privacy</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="plan">Plan</TabsTrigger>
          <TabsTrigger value="danger">Danger</TabsTrigger>
        </TabsList>

        <TabsContent value="account">
          <AccountTab />
        </TabsContent>
        <TabsContent value="privacy">
          <PrivacyTab />
        </TabsContent>
        <TabsContent value="notifications">
          <NotificationsTab />
        </TabsContent>
        <TabsContent value="appearance">
          <AppearanceTab />
        </TabsContent>
        <TabsContent value="plan">
          <PlanTab />
        </TabsContent>
        <TabsContent value="danger">
          <DangerTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AccountTab() {
  const auth = useAuth();
  const user = auth.status === "authed" ? auth.user : null;
  const [signingOut, setSigningOut] = useState(false);
  if (!user) return null;
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Your sign-in identity.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="account-email">Email</Label>
            <Input id="account-email" value={user.email} readOnly disabled />
          </div>
          {user.full_name ? (
            <div className="space-y-2">
              <Label htmlFor="account-name">Display name</Label>
              <Input id="account-name" value={user.full_name} readOnly disabled />
            </div>
          ) : null}
          <p className="text-[13px] text-ink-subtle">
            Email or display-name changes are not yet self-service. Email{" "}
            <a href="mailto:support@aidwiseai.pk" className="text-lapis underline underline-offset-2">
              support@aidwiseai.pk
            </a>{" "}
            and we&rsquo;ll handle it.
          </p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
          <CardDescription>Sign out of AidwiseAI on this device.</CardDescription>
        </CardHeader>
        <CardBody>
          <Button
            variant="secondary"
            loading={signingOut}
            onClick={async () => {
              setSigningOut(true);
              try {
                if (auth.status === "authed") await auth.logout();
              } catch {
                toast.error("Couldn't sign out cleanly. Tokens cleared anyway.");
              }
            }}
          >
            Sign out
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}

function PrivacyTab() {
  const consentQ = useQuery({ queryKey: ["consent"], queryFn: endpoints.legal.consentState });
  const [marketing, setMarketing] = useState<boolean>(false);
  const [b2bShare, setB2bShare] = useState<boolean>(false);

  useEffect(() => {
    if (!consentQ.data) return;
    /* eslint-disable react-hooks/set-state-in-effect */
    setMarketing(Boolean(consentQ.data.records.find((r) => r.consent_type === "marketing")?.granted));
    setB2bShare(Boolean(consentQ.data.records.find((r) => r.consent_type === "b2b_share")?.granted));
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [consentQ.data]);

  const grant = useMutation<ConsentState, Error, { consent_type: "marketing" | "b2b_share"; granted: boolean }>({
    mutationFn: (v) =>
      endpoints.legal.grant({
        consent_type: v.consent_type,
        version: consentQ.data?.current_versions[v.consent_type] || "1.0",
        granted: v.granted,
      }),
    onSuccess: () => toast.success("Saved."),
    onError: () => toast.error("Couldn't save consent. Try again."),
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Cookies</CardTitle>
          <CardDescription>
            Essential cookies always run. Reopen the banner to change analytics, marketing, or
            institution sharing.
          </CardDescription>
        </CardHeader>
        <CardBody>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              const existing = readConsent();
              if (!existing) return;
              writeConsent({
                analytics: existing.analytics,
                marketing: existing.marketing,
                b2b: existing.b2b,
              });
              // Force the banner state to reopen by clearing storage.
              localStorage.removeItem("aidwise.cookie_consent");
              window.dispatchEvent(new Event("storage"));
              window.location.reload();
            }}
          >
            Reopen cookie preferences
          </Button>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Communications</CardTitle>
          <CardDescription>Email me when scholarships matching my profile open.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <ToggleRow
            id="pref-marketing"
            label="Marketing emails"
            description="You can unsubscribe anytime from the footer of any email."
            checked={marketing}
            onChange={(v) => {
              setMarketing(v);
              grant.mutate({ consent_type: "marketing", granted: v });
            }}
          />
          <ToggleRow
            id="pref-b2b"
            label="B2B sharing"
            description="Allow Pro+ to share an anonymised snapshot with universities that have signed a DPA."
            checked={b2bShare}
            onChange={(v) => {
              setB2bShare(v);
              grant.mutate({ consent_type: "b2b_share", granted: v });
            }}
            helper="Available on Pro and Elite."
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Consent history</CardTitle>
          <CardDescription>The latest version you agreed to, per document.</CardDescription>
        </CardHeader>
        <CardBody>
          {consentQ.isLoading ? (
            <p className="text-[13px] text-ink-muted">Loading…</p>
          ) : consentQ.data && consentQ.data.records.length > 0 ? (
            <ul className="divide-y divide-[var(--color-border-quiet)]">
              {consentQ.data.records.map((r) => (
                <li
                  key={r.consent_type}
                  className="flex flex-wrap items-center justify-between gap-2 py-2 text-[13px]"
                >
                  <span className="text-ink">{r.consent_type}</span>
                  <span className="font-mono text-[12px] text-ink-muted">
                    v{r.version} · {r.granted ? "granted" : "withdrawn"} ·{" "}
                    {formatDate(r.granted_at)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[13px] text-ink-muted">No consent records yet.</p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Data export</CardTitle>
          <CardDescription>Request a copy of everything we hold on you.</CardDescription>
        </CardHeader>
        <CardBody>
          <DataExportControl />
        </CardBody>
      </Card>
    </div>
  );
}

function DataExportControl() {
  const [requested, setRequested] = useState<DataExportResponse | null>(null);
  const m = useMutation<DataExportResponse, Error, void>({
    mutationFn: () => endpoints.privacy.requestExport(),
    onSuccess: (r) => {
      setRequested(r);
      toast.success("Export requested. We'll email you when it's ready.");
    },
    onError: () => toast.error("Couldn't request an export. Try again."),
  });
  if (requested) {
    return (
      <div className="space-y-2 text-[13px] text-ink-muted">
        <p>
          Request <code className="font-mono">{requested.id.slice(0, 8)}</code> is{" "}
          <strong className="text-ink-deep">{requested.status}</strong>.
        </p>
        {requested.download_url ? (
          <a className="text-lapis underline underline-offset-2" href={requested.download_url}>
            Download your export
          </a>
        ) : (
          <p>We&rsquo;ll email a download link when it&rsquo;s ready (usually under 1 hour).</p>
        )}
      </div>
    );
  }
  return (
    <Button variant="secondary" loading={m.isPending} onClick={() => m.mutate()}>
      Export my data
    </Button>
  );
}

function NotificationsTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>
          We send deadline reminders for tracked applications and alerts when matching scholarships
          open.
        </CardDescription>
      </CardHeader>
      <CardBody className="space-y-4">
        <ToggleRow
          id="notif-email-digest"
          label="Email digest"
          description="Weekly summary of new matches and approaching deadlines."
          checked
          onChange={() => toast("Per-channel toggles ship in the next release.")}
          disabled
        />
        <ToggleRow
          id="notif-deadlines"
          label="Deadline reminders"
          description="Email 14 days, 7 days, and 1 day before each tracker deadline."
          checked
          onChange={() => toast("Per-channel toggles ship in the next release.")}
          disabled
        />
        <ToggleRow
          id="notif-whatsapp"
          label="WhatsApp alerts"
          description="Available on Elite. Receive priority alerts on WhatsApp."
          checked={false}
          onChange={() => toast("Upgrade to Elite to enable WhatsApp alerts.")}
          disabled
          helper="Elite only."
        />
      </CardBody>
    </Card>
  );
}

function AppearanceTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Appearance</CardTitle>
        <CardDescription>Density and motion. Premium Cultural is ivory-only in v1.</CardDescription>
      </CardHeader>
      <CardBody className="space-y-4">
        <ToggleRow
          id="appearance-compact"
          label="Compact density"
          description="Tighter rows on tracker and admin tables. Defaults remain comfortable."
          checked={false}
          onChange={() => toast("Density toggle ships with the admin table refresh.")}
          disabled
        />
        <ToggleRow
          id="appearance-motion"
          label="Reduced motion"
          description="Follows your OS preference. Override here if you want it on always."
          checked={false}
          onChange={() => toast("OS preference is honoured automatically.")}
          disabled
          helper="Auto"
        />
      </CardBody>
    </Card>
  );
}

function PlanTab() {
  const auth = useAuth();
  if (auth.status !== "authed") return null;
  const user = auth.user;
  const planLabel = PLAN_LABEL[user.plan ?? "free"] ?? user.plan;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Plan</CardTitle>
        <CardDescription>What you have today, and how to change it.</CardDescription>
      </CardHeader>
      <CardBody className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-[12px] uppercase tracking-[0.06em] text-ink-subtle">
            Current
          </span>
          <Badge tone="lapis">{planLabel}</Badge>
          {user.plan_expires_at ? (
            <span className="font-mono text-[12px] text-ink-muted">
              expires {formatDate(user.plan_expires_at)}
            </span>
          ) : null}
        </div>
        {user.billing_country ? (
          <p className="text-[13px] text-ink-muted">
            Billed in <strong className="text-ink-deep">{user.plan_currency ?? "PKR"}</strong> from{" "}
            {user.billing_country}.
          </p>
        ) : null}
        <Button asChild variant="secondary">
          <Link href="/upgrade">See pricing</Link>
        </Button>
      </CardBody>
    </Card>
  );
}

function DangerTab() {
  const auth = useAuth();
  const [scheduled, setScheduled] = useState<DataDeletionRequestResponse | null>(null);
  const qc = useQueryClient();

  const schedule = useMutation<DataDeletionRequestResponse, Error, void>({
    mutationFn: () => endpoints.privacy.scheduleDeletion({}),
    onSuccess: (r) => {
      setScheduled(r);
      toast.success("Deletion scheduled. You have 30 days to cancel.");
    },
    onError: () => toast.error("Couldn't schedule deletion. Try again or email support."),
  });

  const cancel = useMutation<void, Error, void>({
    mutationFn: () => endpoints.privacy.cancelDeletion(),
    onSuccess: () => {
      setScheduled(null);
      toast.success("Deletion cancelled.");
      qc.invalidateQueries({ queryKey: ["consent"] });
    },
    onError: () => toast.error("Couldn't cancel deletion."),
  });

  if (auth.status !== "authed") return null;

  if (scheduled && !scheduled.cancelled_at) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Deletion scheduled</CardTitle>
          <CardDescription>
            Your account will be deleted on{" "}
            <strong className="text-ink-deep">{formatDate(scheduled.scheduled_for)}</strong>. Cancel
            below at any time before then.
          </CardDescription>
        </CardHeader>
        <CardBody>
          <Button variant="secondary" loading={cancel.isPending} onClick={() => cancel.mutate()}>
            Cancel deletion
          </Button>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Danger zone</CardTitle>
        <CardDescription>
          Deleting your account schedules a 30-day window. We retain consent audit logs for 7 years
          per PDPB.
        </CardDescription>
      </CardHeader>
      <CardBody>
        <TypedConfirm
          phrase="DELETE MY ACCOUNT"
          description="Type the phrase exactly to enable the delete button. You can cancel up to 30 days after submission."
          buttonLabel="Delete my account"
          destructive
          onConfirm={async () => {
            await schedule.mutateAsync();
          }}
        />
      </CardBody>
    </Card>
  );
}

function ToggleRow({
  id,
  label,
  description,
  checked,
  onChange,
  helper,
  disabled,
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  helper?: string;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[var(--color-border-quiet)] py-3 last:border-b-0 last:pb-0">
      <div className="min-w-0">
        <p className="text-[14px] font-medium text-ink-deep">{label}</p>
        <p className="mt-1 text-[12px] leading-[1.5] text-ink-muted">{description}</p>
        {helper ? (
          <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            {helper}
          </p>
        ) : null}
      </div>
      <label
        htmlFor={id}
        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors ${
          disabled ? "bg-paper-edge opacity-60" : checked ? "bg-lapis" : "bg-paper-edge"
        }`}
      >
        <input
          id={id}
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange(e.target.checked)}
          className="peer sr-only"
        />
        <span
          aria-hidden
          className={`size-4 rounded-full bg-paper-white shadow transition-transform ${
            checked ? "translate-x-[18px]" : "translate-x-0.5"
          }`}
        />
      </label>
    </div>
  );
}
