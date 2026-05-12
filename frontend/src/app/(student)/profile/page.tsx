"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { StudentProfile } from "@/lib/api";
import { cn } from "@/lib/utils";

const FIELD_TAGS = [
  "Data Science",
  "AI / Machine Learning",
  "Analytics",
  "Computer Science",
  "Statistics",
  "Mathematics",
  "Other",
];

const COUNTRIES = [
  { code: "PK", label: "Pakistan" },
  { code: "IN", label: "India" },
  { code: "BD", label: "Bangladesh" },
  { code: "NG", label: "Nigeria" },
  { code: "EG", label: "Egypt" },
  { code: "CA", label: "Canada" },
  { code: "US", label: "United States" },
];

const TARGET_COUNTRIES = [
  { code: "GB", label: "United Kingdom" },
  { code: "US", label: "United States" },
  { code: "CA", label: "Canada" },
  { code: "DE", label: "Germany" },
  { code: "AU", label: "Australia" },
];

const TESTS = ["IELTS", "TOEFL", "PTE", "Duolingo"] as const;

type Form = {
  citizenship_country_code: string;
  target_country_code: string;
  gpa_value: string;
  gpa_scale: string;
  target_degree_level: "BS" | "MS" | "PHD";
  target_field: string;
  language_test_type: string;
  language_test_score: string;
};

function fromProfile(p: StudentProfile | undefined): Form {
  return {
    citizenship_country_code: p?.citizenship_country_code ?? "",
    target_country_code: p?.target_country_code ?? "GB",
    gpa_value: p?.gpa_value != null ? String(p.gpa_value) : "",
    gpa_scale: p?.gpa_scale != null ? String(p.gpa_scale) : "4.0",
    target_degree_level: p?.target_degree_level ?? "MS",
    target_field: p?.target_field ?? "",
    language_test_type: p?.language_test_type ?? "",
    language_test_score: p?.language_test_score != null ? String(p.language_test_score) : "",
  };
}

function toPayload(form: Form): Partial<StudentProfile> {
  return {
    citizenship_country_code: form.citizenship_country_code,
    target_country_code: form.target_country_code,
    gpa_value: form.gpa_value ? Number(form.gpa_value) : null,
    gpa_scale: form.gpa_scale ? Number(form.gpa_scale) : 4.0,
    target_degree_level: form.target_degree_level,
    target_field: form.target_field,
    language_test_type: form.language_test_type || null,
    language_test_score: form.language_test_score ? Number(form.language_test_score) : null,
  };
}

export default function ProfilePage() {
  const qc = useQueryClient();
  const profileQ = useQuery({ queryKey: ["profile"], queryFn: endpoints.profile.get, retry: false });
  const [form, setForm] = useState<Form>(fromProfile(undefined));
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (profileQ.data && !hydrated) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setForm(fromProfile(profileQ.data));
      setHydrated(true);
    }
  }, [profileQ.data, hydrated]);

  const mut = useMutation({
    mutationFn: (payload: Partial<StudentProfile>) => endpoints.profile.upsert(payload),
    onMutate: async (payload) => {
      await qc.cancelQueries({ queryKey: ["profile"] });
      const prev = qc.getQueryData<StudentProfile>(["profile"]);
      qc.setQueryData<StudentProfile | undefined>(["profile"], (old) =>
        old ? { ...old, ...payload } : (payload as StudentProfile),
      );
      return { prev };
    },
    onError: (err, _payload, ctx) => {
      qc.setQueryData(["profile"], ctx?.prev);
      const msg = err instanceof Error ? err.message : "Couldn't save. Try again.";
      toast.error(msg);
    },
    onSuccess: (data) => {
      qc.setQueryData(["profile"], data);
      qc.invalidateQueries({ queryKey: ["recommendations"] });
      toast.success("Profile saved.");
    },
  });

  const update = <K extends keyof Form>(k: K, v: Form[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const valid =
    form.citizenship_country_code.length === 2 &&
    form.target_country_code.length === 2 &&
    form.target_field.trim().length >= 2 &&
    !!form.target_degree_level;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid) {
      toast.error("Fill citizenship, target country, target degree, and at least one field.");
      return;
    }
    mut.mutate(toPayload(form));
  };

  if (profileQ.isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  const fieldTags = form.target_field.split(",").map((t) => t.trim()).filter(Boolean);
  const toggleTag = (t: string) => {
    const next = fieldTags.includes(t) ? fieldTags.filter((x) => x !== t) : [...fieldTags, t];
    update("target_field", next.join(", "));
  };

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="font-display text-3xl text-ink">Your profile</h1>
        <p className="mt-1 text-ink-muted">
          Eligibility runs on this. Changes feed straight into your matches.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Citizenship and target</CardTitle>
          <CardDescription>Required for eligibility filtering.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="citizenship">Citizenship</Label>
            <select
              id="citizenship"
              value={form.citizenship_country_code}
              onChange={(e) => update("citizenship_country_code", e.target.value)}
              className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
              required
            >
              <option value="">Pick one</option>
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="target_country">Target country</Label>
            <select
              id="target_country"
              value={form.target_country_code}
              onChange={(e) => update("target_country_code", e.target.value)}
              className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
              required
            >
              {TARGET_COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Academic</CardTitle>
          <CardDescription>GPA and target degree drive eligibility filters.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="gpa">GPA</Label>
            <div className="flex items-center gap-2">
              <Input
                id="gpa"
                value={form.gpa_value}
                inputMode="decimal"
                placeholder="3.6"
                onChange={(e) => update("gpa_value", e.target.value)}
                className="max-w-[140px]"
              />
              <span className="text-ink-muted">on a</span>
              <select
                value={form.gpa_scale}
                onChange={(e) => update("gpa_scale", e.target.value)}
                className="h-11 rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
              >
                <option value="4.0">4.0 scale</option>
                <option value="5.0">5.0 scale</option>
                <option value="10.0">10 scale</option>
                <option value="100">100 scale</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Target degree</Label>
            <div className="flex flex-wrap gap-2">
              {(["BS", "MS", "PHD"] as const).map((d) => (
                <Chip
                  key={d}
                  active={form.target_degree_level === d}
                  onClick={() => update("target_degree_level", d)}
                >
                  {d}
                </Chip>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Field tags</Label>
            <div className="flex flex-wrap gap-2">
              {FIELD_TAGS.map((t) => (
                <Chip key={t} active={fieldTags.includes(t)} onClick={() => toggleTag(t)}>
                  {t}
                </Chip>
              ))}
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Language test</CardTitle>
          <CardDescription>Optional English-proficiency score.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="flex items-center gap-2">
            <select
              value={form.language_test_type}
              onChange={(e) => update("language_test_type", e.target.value)}
              className="h-11 rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
            >
              <option value="">None</option>
              {TESTS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <Input
              value={form.language_test_score}
              inputMode="decimal"
              placeholder="Score"
              onChange={(e) => update("language_test_score", e.target.value)}
              className="max-w-[160px]"
              aria-label="Score"
              disabled={!form.language_test_type}
            />
          </div>
        </CardBody>
      </Card>

      <div className="sticky bottom-4 flex items-center justify-end gap-3 rounded-[16px] border border-[var(--color-border)] bg-paper-white/95 p-3 backdrop-blur">
        <Button type="submit" loading={mut.isPending} disabled={!valid}>
          <Check className="size-4" strokeWidth={2} /> Save changes
        </Button>
      </div>
    </form>
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
