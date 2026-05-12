"use client";

import { Check, Minus, X } from "lucide-react";
import type { Scholarship, StudentProfile } from "@/lib/api";

type Status = "pass" | "fail" | "unknown";

type Row = {
  axis: string;
  status: Status;
  student: string;
  required: string;
};

function evaluate(s: Scholarship, p: StudentProfile | undefined): Row[] {
  const rows: Row[] = [];

  // Citizenship
  if (s.citizenship_rules && s.citizenship_rules.length > 0) {
    const req = s.citizenship_rules.join(", ");
    if (!p?.citizenship) {
      rows.push({ axis: "Citizenship", status: "unknown", student: "Not set", required: req });
    } else {
      const ok = s.citizenship_rules.includes(p.citizenship) || s.citizenship_rules.includes("ANY");
      rows.push({
        axis: "Citizenship",
        status: ok ? "pass" : "fail",
        student: p.citizenship,
        required: req,
      });
    }
  } else {
    rows.push({
      axis: "Citizenship",
      status: "pass",
      student: p?.citizenship ?? "—",
      required: "Any",
    });
  }

  // Degree
  rows.push({
    axis: "Degree",
    status: !p?.degree_level
      ? "unknown"
      : p.degree_level === s.degree_level
        ? "pass"
        : "fail",
    student: p?.degree_level ?? "Not set",
    required: s.degree_level,
  });

  // GPA
  if (s.min_gpa != null) {
    if (p?.gpa == null || p.gpa_scale == null) {
      rows.push({
        axis: "GPA",
        status: "unknown",
        student: "Not set",
        required: `≥ ${s.min_gpa}`,
      });
    } else {
      const normalized = (p.gpa / p.gpa_scale) * 4.0;
      rows.push({
        axis: "GPA",
        status: normalized >= s.min_gpa ? "pass" : "fail",
        student: `${p.gpa}/${p.gpa_scale}`,
        required: `≥ ${s.min_gpa}`,
      });
    }
  } else {
    rows.push({
      axis: "GPA",
      status: "pass",
      student: p?.gpa != null ? `${p.gpa}/${p.gpa_scale ?? "?"}` : "—",
      required: "Any",
    });
  }

  // Field
  if (s.field_tags.length > 0) {
    const overlap = (p?.field_tags ?? []).some((t) => s.field_tags.includes(t));
    rows.push({
      axis: "Field",
      status: !p?.field_tags
        ? "unknown"
        : overlap
          ? "pass"
          : "fail",
      student: (p?.field_tags ?? []).slice(0, 2).join(", ") || "Not set",
      required: s.field_tags.slice(0, 2).join(", ") + (s.field_tags.length > 2 ? "…" : ""),
    });
  }

  // Language
  if (s.language_requirements && s.language_requirements.length > 0) {
    const studentScores = p?.language_scores ?? [];
    const req = s.language_requirements
      .map((r) => `${r.test} ${r.min_score}+`)
      .join(", ");
    if (studentScores.length === 0) {
      rows.push({ axis: "Language", status: "unknown", student: "Not set", required: req });
    } else {
      const ok = s.language_requirements.some((r) => {
        const have = studentScores.find((x) => x.test === r.test);
        return have && have.score >= r.min_score;
      });
      rows.push({
        axis: "Language",
        status: ok ? "pass" : "fail",
        student: studentScores.map((x) => `${x.test} ${x.score}`).join(", "),
        required: req,
      });
    }
  }

  return rows;
}

export function EligibilityMatrix({
  scholarship,
  profile,
}: {
  scholarship: Scholarship;
  profile: StudentProfile | undefined;
}) {
  const rows = evaluate(scholarship, profile);
  return (
    <div className="rounded-[12px] border border-[var(--color-border)]">
      <table className="w-full text-sm">
        <tbody>
          {rows.map((r) => (
            <tr key={r.axis} className="border-b border-[var(--color-border)] last:border-b-0">
              <td className="w-32 px-3 py-2 font-mono text-xs uppercase tracking-wider text-ink-subtle">
                {r.axis}
              </td>
              <td className="px-3 py-2 text-ink">{r.student}</td>
              <td className="px-3 py-2 text-ink-muted">{r.required}</td>
              <td className="w-10 px-3 py-2 text-right">
                <StatusIcon status={r.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusIcon({ status }: { status: Status }) {
  if (status === "pass") {
    return (
      <span
        className="inline-flex size-6 items-center justify-center rounded-full bg-validated-soft text-validated"
        aria-label="Eligible"
      >
        <Check className="size-3.5" strokeWidth={2.5} />
      </span>
    );
  }
  if (status === "fail") {
    return (
      <span
        className="inline-flex size-6 items-center justify-center rounded-full bg-danger-soft text-danger"
        aria-label="Not eligible"
      >
        <X className="size-3.5" strokeWidth={2.5} />
      </span>
    );
  }
  return (
    <span
      className="inline-flex size-6 items-center justify-center rounded-full bg-paper-warm text-ink-subtle"
      aria-label="Unknown"
    >
      <Minus className="size-3.5" strokeWidth={2.5} />
    </span>
  );
}
