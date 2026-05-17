"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/ui/section-header";
import { StickySaveFooter } from "@/components/profile/StickySaveFooter";
import { MultiChip } from "@/components/profile/MultiChip";
import { endpoints } from "@/lib/api";
import type { StudentProfile } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";

/**
 * /profile — Front-upgrade §6.22. Six cards:
 *   1. Contact            (email locked, city_of_origin)
 *   2. Academic record    (Pakistani uni, HEC degree level, CGPA scale, degree subject, grad year, GPA, target degree)
 *   3. Test scores        (IELTS / TOEFL / GRE Q+V; legacy language_test_type still wired for back-compat)
 *   4. Your goal          (target_countries multi, target_fields multi, intake, funding requirement)
 *   5. Aspirations        (research publications + count)
 *   6. Background         (3 boolean financial-context flags)
 *
 * StickySaveFooter slides up when form is dirty. Save fires a single
 * PATCH with the full payload; backend reconciles single-vs-multi country
 * field server-side.
 */

const TARGET_COUNTRIES: { value: string; label: string }[] = [
  { value: "GB", label: "United Kingdom" },
  { value: "US", label: "United States" },
  { value: "CA", label: "Canada" },
  { value: "DE", label: "Germany" },
  { value: "AU", label: "Australia" },
];

const TARGET_FIELDS: { value: string; label: string }[] = [
  { value: "Computer Science", label: "Computer Science" },
  { value: "Data Science", label: "Data Science" },
  { value: "AI / ML", label: "AI / ML" },
  { value: "Electrical Engineering", label: "Electrical Engineering" },
  { value: "Mechanical Engineering", label: "Mechanical Engineering" },
  { value: "Economics", label: "Economics" },
  { value: "Public Policy", label: "Public Policy" },
  { value: "Biotechnology", label: "Biotechnology" },
  { value: "Mathematics", label: "Mathematics" },
  { value: "Statistics", label: "Statistics" },
];

const CITIZENSHIP: { code: string; label: string }[] = [
  { code: "PK", label: "Pakistan" },
  { code: "IN", label: "India" },
  { code: "BD", label: "Bangladesh" },
  { code: "NG", label: "Nigeria" },
  { code: "EG", label: "Egypt" },
];

type Form = {
  // Card 1
  citizenship_country_code: string;
  city_of_origin: string;
  // Card 2
  pakistani_university: string;
  hec_degree_level: string;
  cgpa_scale_choice: string;
  degree_subject: string;
  graduation_year: string;
  gpa_value: string;
  gpa_scale: string;
  target_degree_level: string;
  // Card 3
  ielts_score: string;
  toefl_score: string;
  gre_quant: string;
  gre_verbal: string;
  language_test_type: string;
  language_test_score: string;
  // Card 4
  target_countries: string[];
  target_fields: string[];
  target_field_primary: string;
  intake_target: string;
  funding_requirement: string;
  // Card 5
  has_research_publications: "yes" | "no" | "";
  research_publication_count: string;
  // Card 6
  can_afford_application_fees: "yes" | "no" | "";
  needs_gre_waiver: "yes" | "no" | "";
  family_has_funds_for_bank_statement: "yes" | "no" | "";
};

const EMPTY: Form = {
  citizenship_country_code: "PK",
  city_of_origin: "",
  pakistani_university: "",
  hec_degree_level: "",
  cgpa_scale_choice: "",
  degree_subject: "",
  graduation_year: "",
  gpa_value: "",
  gpa_scale: "4.0",
  target_degree_level: "MS",
  ielts_score: "",
  toefl_score: "",
  gre_quant: "",
  gre_verbal: "",
  language_test_type: "",
  language_test_score: "",
  target_countries: [],
  target_fields: [],
  target_field_primary: "",
  intake_target: "",
  funding_requirement: "",
  has_research_publications: "",
  research_publication_count: "",
  can_afford_application_fees: "",
  needs_gre_waiver: "",
  family_has_funds_for_bank_statement: "",
};

const boolOrNull = (v: string): boolean | null => (v === "yes" ? true : v === "no" ? false : null);
const numOrNull = (v: string): number | null => (v.trim() === "" ? null : Number(v));
const strOrNull = (v: string): string | null => (v.trim() === "" ? null : v.trim());

function fromProfile(p: StudentProfile | undefined): Form {
  if (!p) return EMPTY;
  return {
    citizenship_country_code: p.citizenship_country_code || "PK",
    city_of_origin: p.city_of_origin ?? "",
    pakistani_university: p.pakistani_university ?? "",
    hec_degree_level: p.hec_degree_level ?? "",
    cgpa_scale_choice: p.cgpa_scale_choice ?? "",
    degree_subject: p.degree_subject ?? "",
    graduation_year: p.graduation_year != null ? String(p.graduation_year) : "",
    gpa_value: p.gpa_value != null ? String(p.gpa_value) : "",
    gpa_scale: String(p.gpa_scale ?? 4.0),
    target_degree_level: p.target_degree_level || "MS",
    ielts_score: p.ielts_score != null ? String(p.ielts_score) : "",
    toefl_score: p.toefl_score != null ? String(p.toefl_score) : "",
    gre_quant: p.gre_quant != null ? String(p.gre_quant) : "",
    gre_verbal: p.gre_verbal != null ? String(p.gre_verbal) : "",
    language_test_type: p.language_test_type ?? "",
    language_test_score: p.language_test_score != null ? String(p.language_test_score) : "",
    target_countries: p.target_countries?.length ? p.target_countries : p.target_country_code ? [p.target_country_code] : [],
    target_fields: p.target_fields?.length ? p.target_fields : p.target_field ? [p.target_field] : [],
    target_field_primary: p.target_field || "",
    intake_target: p.intake_target ?? "",
    funding_requirement: p.funding_requirement ?? "",
    has_research_publications:
      p.has_research_publications == null ? "" : p.has_research_publications ? "yes" : "no",
    research_publication_count:
      p.research_publication_count != null ? String(p.research_publication_count) : "",
    can_afford_application_fees:
      p.can_afford_application_fees == null ? "" : p.can_afford_application_fees ? "yes" : "no",
    needs_gre_waiver: p.needs_gre_waiver == null ? "" : p.needs_gre_waiver ? "yes" : "no",
    family_has_funds_for_bank_statement:
      p.family_has_funds_for_bank_statement == null
        ? ""
        : p.family_has_funds_for_bank_statement
          ? "yes"
          : "no",
  };
}

function toPayload(form: Form): Partial<StudentProfile> {
  return {
    citizenship_country_code: form.citizenship_country_code,
    city_of_origin: strOrNull(form.city_of_origin),
    pakistani_university: strOrNull(form.pakistani_university),
    hec_degree_level: (strOrNull(form.hec_degree_level) as StudentProfile["hec_degree_level"]) ?? null,
    cgpa_scale_choice: (strOrNull(form.cgpa_scale_choice) as StudentProfile["cgpa_scale_choice"]) ?? null,
    degree_subject: strOrNull(form.degree_subject),
    graduation_year: numOrNull(form.graduation_year),
    gpa_value: numOrNull(form.gpa_value),
    gpa_scale: Number(form.gpa_scale) || 4.0,
    target_degree_level: (form.target_degree_level as StudentProfile["target_degree_level"]) || "MS",
    ielts_score: numOrNull(form.ielts_score),
    toefl_score: numOrNull(form.toefl_score),
    gre_quant: numOrNull(form.gre_quant),
    gre_verbal: numOrNull(form.gre_verbal),
    language_test_type: strOrNull(form.language_test_type),
    language_test_score: numOrNull(form.language_test_score),
    target_countries: form.target_countries,
    target_country_code: form.target_countries[0] ?? "",
    target_fields: form.target_fields,
    target_field: form.target_field_primary || form.target_fields[0] || "",
    intake_target: (strOrNull(form.intake_target) as StudentProfile["intake_target"]) ?? null,
    funding_requirement:
      (strOrNull(form.funding_requirement) as StudentProfile["funding_requirement"]) ?? null,
    has_research_publications: boolOrNull(form.has_research_publications),
    research_publication_count:
      form.has_research_publications === "yes" ? numOrNull(form.research_publication_count) : null,
    can_afford_application_fees: boolOrNull(form.can_afford_application_fees),
    needs_gre_waiver: boolOrNull(form.needs_gre_waiver),
    family_has_funds_for_bank_statement: boolOrNull(form.family_has_funds_for_bank_statement),
  };
}

const selectCls =
  "h-11 w-full rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 text-[14px] text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]";

export default function ProfilePage() {
  const qc = useQueryClient();
  const auth = useAuth();
  const profileQ = useQuery({ queryKey: ["profile"], queryFn: endpoints.profile.get, retry: false });
  const initial = useMemo(() => fromProfile(profileQ.data), [profileQ.data]);
  const [form, setForm] = useState<Form>(initial);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (profileQ.data && !hydrated) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setForm(fromProfile(profileQ.data));
      setHydrated(true);
    }
  }, [profileQ.data, hydrated]);

  const dirty = useMemo(() => JSON.stringify(form) !== JSON.stringify(initial), [form, initial]);

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
    onError: (err, _p, ctx) => {
      qc.setQueryData(["profile"], ctx?.prev);
      const msg = err instanceof Error ? err.message : "Couldn't save. Try again.";
      toast.error(msg);
    },
    onSuccess: (data) => {
      qc.setQueryData(["profile"], data);
      qc.invalidateQueries({ queryKey: ["recommendations"] });
      qc.invalidateQueries({ queryKey: ["scholarships", "match"] });
      toast.success("Profile saved.");
    },
  });

  const set = <K extends keyof Form>(k: K, v: Form[K]) => setForm((f) => ({ ...f, [k]: v }));

  const toggleCountry = (code: string) =>
    setForm((f) => ({
      ...f,
      target_countries: f.target_countries.includes(code)
        ? f.target_countries.filter((c) => c !== code)
        : [...f.target_countries, code],
    }));

  const toggleField = (val: string) =>
    setForm((f) => ({
      ...f,
      target_fields: f.target_fields.includes(val)
        ? f.target_fields.filter((c) => c !== val)
        : [...f.target_fields, val],
      target_field_primary: !f.target_field_primary && !f.target_fields.includes(val) ? val : f.target_field_primary,
    }));

  const valid =
    form.citizenship_country_code.length === 2 &&
    form.target_countries.length > 0 &&
    form.target_fields.length > 0 &&
    !!form.target_degree_level;

  const onSave = () => {
    if (!valid) {
      toast.error("Pick citizenship, at least one target country, and one target field.");
      return;
    }
    mut.mutate(toPayload(form));
  };

  const userEmail = auth.status === "authed" ? auth.user.email : null;

  if (profileQ.isLoading) {
    return (
      <div className="mx-auto max-w-[760px] space-y-4">
        <Skeleton className="h-10 w-48" />
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-44 w-full rounded-[18px]" />
        ))}
      </div>
    );
  }

  return (
    <form
      data-testid="profile-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSave();
      }}
      className="mx-auto max-w-[760px] space-y-6"
    >
      <PageHeader
        title="Profile"
        description="Matches, SOPs, and B2B snapshots all read from this. Update whenever your plan shifts."
      />

      {/* Card 1 — Contact */}
      <Card>
        <CardHeader>
          <CardTitle>Contact</CardTitle>
          <CardDescription>Your sign-in identity. Email changes need support.</CardDescription>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label="Email" id="email">
            <Input id="email" value={userEmail ?? ""} readOnly disabled />
          </Field>
          <Field label="Citizenship" id="citizenship">
            <select
              id="citizenship"
              value={form.citizenship_country_code}
              onChange={(e) => set("citizenship_country_code", e.target.value)}
              className={selectCls}
              required
            >
              {CITIZENSHIP.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="City of origin" id="city" hint="Used for B2B snapshots; never on public profile.">
            <Input
              id="city"
              value={form.city_of_origin}
              onChange={(e) => set("city_of_origin", e.target.value)}
              placeholder="e.g. Karachi"
            />
          </Field>
        </CardBody>
      </Card>

      {/* Card 2 — Academic record */}
      <Card>
        <CardHeader>
          <CardTitle>Academic record</CardTitle>
          <CardDescription>HEC fields drive Pakistan-pivot eligibility.</CardDescription>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label="Pakistani university" id="pak-uni">
            <Input
              id="pak-uni"
              value={form.pakistani_university}
              onChange={(e) => set("pakistani_university", e.target.value)}
              placeholder="e.g. NUST, LUMS, FAST"
            />
          </Field>
          <Field label="HEC degree level" id="hec-deg">
            <select
              id="hec-deg"
              value={form.hec_degree_level}
              onChange={(e) => set("hec_degree_level", e.target.value)}
              className={selectCls}
            >
              <option value="">—</option>
              <option value="bachelor">Bachelor</option>
              <option value="master">Master</option>
              <option value="mphil">MPhil</option>
            </select>
          </Field>
          <Field label="Degree subject" id="deg-subj">
            <Input
              id="deg-subj"
              value={form.degree_subject}
              onChange={(e) => set("degree_subject", e.target.value)}
              placeholder="e.g. Computer Science"
            />
          </Field>
          <Field label="Graduation year" id="grad-year">
            <Input
              id="grad-year"
              type="number"
              inputMode="numeric"
              min={1950}
              max={2100}
              value={form.graduation_year}
              onChange={(e) => set("graduation_year", e.target.value)}
              placeholder="e.g. 2024"
            />
          </Field>
          <Field label="CGPA" id="gpa" hint="Type your CGPA on its native scale.">
            <div className="flex items-center gap-2">
              <Input
                id="gpa"
                inputMode="decimal"
                value={form.gpa_value}
                onChange={(e) => set("gpa_value", e.target.value)}
                placeholder="3.6"
                className="max-w-[140px]"
              />
              <select
                value={form.gpa_scale}
                onChange={(e) => set("gpa_scale", e.target.value)}
                className={selectCls}
                aria-label="GPA scale"
              >
                <option value="4.0">on 4.0</option>
                <option value="5.0">on 5.0</option>
                <option value="10.0">on 10</option>
                <option value="100">on 100</option>
              </select>
            </div>
          </Field>
          <Field label="CGPA scale choice" id="cgpa-scale">
            <select
              id="cgpa-scale"
              value={form.cgpa_scale_choice}
              onChange={(e) => set("cgpa_scale_choice", e.target.value)}
              className={selectCls}
            >
              <option value="">—</option>
              <option value="4.0">Standard 4.0</option>
              <option value="4.0_hec">HEC 4.0</option>
            </select>
          </Field>
          <Field label="Target degree" id="target-deg">
            <select
              id="target-deg"
              value={form.target_degree_level}
              onChange={(e) => set("target_degree_level", e.target.value)}
              className={selectCls}
              required
            >
              <option value="BS">Bachelor (BS)</option>
              <option value="MS">Master (MS)</option>
              <option value="MENG">Master of Engineering</option>
              <option value="MBA">MBA</option>
              <option value="PHD">PhD</option>
            </select>
          </Field>
        </CardBody>
      </Card>

      {/* Card 3 — Test scores */}
      <Card>
        <CardHeader>
          <CardTitle>Test scores</CardTitle>
          <CardDescription>Optional. We use these for eligibility caps.</CardDescription>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label="IELTS overall" id="ielts" hint="0.0 – 9.0">
            <Input
              id="ielts"
              inputMode="decimal"
              value={form.ielts_score}
              onChange={(e) => set("ielts_score", e.target.value)}
              placeholder="7.0"
            />
          </Field>
          <Field label="TOEFL iBT" id="toefl" hint="0 – 120">
            <Input
              id="toefl"
              type="number"
              inputMode="numeric"
              value={form.toefl_score}
              onChange={(e) => set("toefl_score", e.target.value)}
              placeholder="95"
            />
          </Field>
          <Field label="GRE Quant" id="gre-q" hint="130 – 170">
            <Input
              id="gre-q"
              type="number"
              inputMode="numeric"
              value={form.gre_quant}
              onChange={(e) => set("gre_quant", e.target.value)}
              placeholder="165"
            />
          </Field>
          <Field label="GRE Verbal" id="gre-v" hint="130 – 170">
            <Input
              id="gre-v"
              type="number"
              inputMode="numeric"
              value={form.gre_verbal}
              onChange={(e) => set("gre_verbal", e.target.value)}
              placeholder="155"
            />
          </Field>
        </CardBody>
      </Card>

      {/* Card 4 — Your goal */}
      <Card>
        <CardHeader>
          <CardTitle>Your goal</CardTitle>
          <CardDescription>Drives match scope. Pick at least one country and field.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-5">
          <div className="space-y-2">
            <Label>Target countries</Label>
            <MultiChip
              options={TARGET_COUNTRIES.map((c) => ({ value: c.value, label: c.label }))}
              selected={form.target_countries}
              onToggle={toggleCountry}
              ariaLabel="Target countries"
            />
          </div>
          <div className="space-y-2">
            <Label>Target fields</Label>
            <MultiChip
              options={TARGET_FIELDS}
              selected={form.target_fields}
              onToggle={toggleField}
              ariaLabel="Target fields"
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Intake target" id="intake">
              <select
                id="intake"
                value={form.intake_target}
                onChange={(e) => set("intake_target", e.target.value)}
                className={selectCls}
              >
                <option value="">—</option>
                <option value="jan_2025">Jan 2025</option>
                <option value="sep_2025">Sep 2025</option>
                <option value="jan_2026">Jan 2026</option>
                <option value="sep_2026">Sep 2026</option>
                <option value="flexible">Flexible</option>
              </select>
            </Field>
            <Field label="Funding requirement" id="fund-req">
              <select
                id="fund-req"
                value={form.funding_requirement}
                onChange={(e) => set("funding_requirement", e.target.value)}
                className={selectCls}
              >
                <option value="">—</option>
                <option value="fully_funded_only">Fully funded only</option>
                <option value="partial_ok">Partial OK</option>
                <option value="self_funded_ok">Self-funded OK</option>
              </select>
            </Field>
          </div>
        </CardBody>
      </Card>

      {/* Card 5 — Aspirations */}
      <Card>
        <CardHeader>
          <CardTitle>Aspirations</CardTitle>
          <CardDescription>Research signals help unlock funded PhD bands.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <Field label="Have research publications?" id="has-pub">
            <YesNo
              id="has-pub"
              value={form.has_research_publications}
              onChange={(v) => set("has_research_publications", v)}
            />
          </Field>
          {form.has_research_publications === "yes" ? (
            <Field label="How many?" id="pub-count">
              <Input
                id="pub-count"
                type="number"
                inputMode="numeric"
                min={0}
                value={form.research_publication_count}
                onChange={(e) => set("research_publication_count", e.target.value)}
                placeholder="e.g. 2"
                className="max-w-[140px]"
              />
            </Field>
          ) : null}
        </CardBody>
      </Card>

      {/* Card 6 — Background */}
      <Card>
        <CardHeader>
          <CardTitle>Background</CardTitle>
          <CardDescription>
            Sensitive categories (religion / politics / biometric) are never collected per PDPB.
          </CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <Field label="Can you afford application fees?" id="afford-fees">
            <YesNo
              id="afford-fees"
              value={form.can_afford_application_fees}
              onChange={(v) => set("can_afford_application_fees", v)}
            />
          </Field>
          <Field label="Need a GRE waiver?" id="gre-waiver">
            <YesNo
              id="gre-waiver"
              value={form.needs_gre_waiver}
              onChange={(v) => set("needs_gre_waiver", v)}
            />
          </Field>
          <Field
            label="Family can show bank statement?"
            id="bank-stmt"
            hint="Required for most US/UK visa categories."
          >
            <YesNo
              id="bank-stmt"
              value={form.family_has_funds_for_bank_statement}
              onChange={(v) => set("family_has_funds_for_bank_statement", v)}
            />
          </Field>
        </CardBody>
      </Card>

      <StickySaveFooter
        dirty={dirty}
        saving={mut.isPending}
        onSave={onSave}
        onReset={() => setForm(initial)}
      />
    </form>
  );
}

function Field({
  label,
  id,
  hint,
  children,
}: {
  label: string;
  id: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint ? <p className="text-[12px] text-ink-subtle">{hint}</p> : null}
    </div>
  );
}

function YesNo({
  id,
  value,
  onChange,
}: {
  id: string;
  value: "yes" | "no" | "";
  onChange: (v: "yes" | "no" | "") => void;
}) {
  return (
    <div role="radiogroup" aria-label={id} className="inline-flex gap-2">
      {(
        [
          { v: "yes" as const, label: "Yes" },
          { v: "no" as const, label: "No" },
        ]
      ).map((opt) => {
        const active = value === opt.v;
        return (
          <button
            key={opt.v}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(active ? "" : opt.v)}
            className={
              active
                ? "inline-flex h-9 items-center rounded-[10px] border border-lapis bg-lapis-soft px-4 text-[13px] text-lapis tap-target"
                : "inline-flex h-9 items-center rounded-[10px] border border-[var(--color-border)] bg-paper-white px-4 text-[13px] text-ink-muted hover:bg-paper-warm hover:text-ink-deep tap-target"
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
