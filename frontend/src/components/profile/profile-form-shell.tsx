"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type { ApiError, StudentProfile } from "@/lib/types";

const FIELD_OPTIONS = [
  "Data Science",
  "Artificial Intelligence",
  "Analytics",
];

const COUNTRY_OPTIONS = [
  { value: "CA", label: "Canada" },
  { value: "US", label: "United States (Fulbright only)" },
];

const DEFAULT_PROFILE: StudentProfile = {
  citizenship_country_code: "PK",
  gpa_value: 3.7,
  gpa_scale: 4,
  target_field: "Data Science",
  target_degree_level: "MS",
  target_country_code: "CA",
  language_test_type: "IELTS",
  language_test_score: 7.5,
};

export function ProfileFormShell() {
  const router = useRouter();
  const { accessToken } = useAuth();
  const [form, setForm] = useState<StudentProfile>(DEFAULT_PROFILE);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let isActive = true;

    const loadProfile = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const existing = await apiRequest<StudentProfile>("/profile", {
          token: accessToken,
        });
        if (isActive) {
          setForm({
            ...existing,
            gpa_value: existing.gpa_value ?? DEFAULT_PROFILE.gpa_value,
            gpa_scale: existing.gpa_scale ?? DEFAULT_PROFILE.gpa_scale,
            language_test_type:
              existing.language_test_type ?? DEFAULT_PROFILE.language_test_type,
            language_test_score:
              existing.language_test_score ?? DEFAULT_PROFILE.language_test_score,
          });
          setMessage(
            "Loaded your saved profile. You can adjust it before rerunning recommendations.",
          );
        }
      } catch (caught) {
        const apiError = caught as ApiError;
        if (apiError.status !== 404 && isActive) {
          setError(apiError.message);
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void loadProfile();

    return () => {
      isActive = false;
    };
  }, [accessToken]);

  const helperNote = useMemo(() => {
    return form.target_country_code === "US"
      ? "US recommendations stay limited to Fulbright-related published records in this MVP."
      : "Canada remains the main MVP target, so the seeded demo set is strongest here.";
  }, [form.target_country_code]);

  const handleChange = (name: keyof StudentProfile, value: string) => {
    setForm((current) => ({
      ...current,
      [name]:
        name === "gpa_value" || name === "gpa_scale" || name === "language_test_score"
          ? value === ""
            ? null
            : Number(value)
          : value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      await apiRequest<StudentProfile>("/profile", {
        method: "PUT",
        token: accessToken,
        body: JSON.stringify({
          ...form,
          target_degree_level: "MS",
        }),
      });
      setMessage("Profile saved. Redirecting to the recommendation workspace.");
      router.push("/recommendations");
    } catch (caught) {
      setError((caught as ApiError).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell
      eyebrow="Profile input"
      title="Save the narrow profile contract that drives the seeded recommendation demo."
      description="This form stays intentionally close to the backend schema so eligibility logic remains deterministic, inspectable, and easy to demo."
    >
      <section className="page-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="Profile contract"
            title="Profile inputs stay narrow and recommendation-focused."
            description="The seeded demo dataset covers Canada-first MS Data Science, AI, and Analytics paths, plus Fulbright-related US scope only."
          />
          <div className="surface-list">
            <article>
              <p className="list-heading">Recommendation inputs</p>
              <p className="body-copy">
                Citizenship, GPA, target country, target field, and optional language evidence are enough for the current deterministic filters.
              </p>
            </article>
            <article>
              <p className="list-heading">Source-of-truth rule</p>
              <p className="body-copy">
                Recommendations will only use published scholarship records. Raw and validated records stay inside the curator workflow.
              </p>
            </article>
          </div>
        </article>

        <article className="surface-panel">
          <div className="meta-row">
            <StatusBadge label="Seeded demo ready" variant="validated" />
            <StatusBadge label="Rules-first" variant="generated" />
          </div>
          <p className="body-copy">{helperNote}</p>
          {message ? <p className="field-note">{message}</p> : null}
          {error ? <p className="form-error">{error}</p> : null}
        </article>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Profile form"
          title="Save your profile, then move directly into recommendations."
          description="The MVP keeps this form short on purpose so the browser demo reaches the recommendation page without a long intake wizard."
        />
        {isLoading ? (
          <p className="body-copy">Loading your saved profile.</p>
        ) : (
          <form
            className="auth-form"
            data-testid="profile-form"
            onSubmit={handleSubmit}
          >
            <div className="form-grid">
              <label className="form-field">
                <span className="form-field__label">Citizenship country</span>
                <input
                  className="text-input"
                  maxLength={2}
                  name="citizenship_country_code"
                  onChange={(event) =>
                    handleChange(
                      "citizenship_country_code",
                      event.target.value.toUpperCase(),
                    )
                  }
                  required
                  value={form.citizenship_country_code}
                />
              </label>

              <label className="form-field">
                <span className="form-field__label">Target country</span>
                <select
                  className="text-input"
                  name="target_country_code"
                  onChange={(event) =>
                    handleChange("target_country_code", event.target.value)
                  }
                  value={form.target_country_code}
                >
                  {COUNTRY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span className="form-field__label">Target field</span>
                <select
                  className="text-input"
                  name="target_field"
                  onChange={(event) => handleChange("target_field", event.target.value)}
                  value={form.target_field}
                >
                  {FIELD_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span className="form-field__label">Degree level</span>
                <input
                  className="text-input"
                  disabled
                  name="target_degree_level"
                  value={form.target_degree_level}
                />
              </label>

              <label className="form-field">
                <span className="form-field__label">GPA value</span>
                <input
                  className="text-input"
                  min="0"
                  name="gpa_value"
                  onChange={(event) => handleChange("gpa_value", event.target.value)}
                  required
                  step="0.01"
                  type="number"
                  value={form.gpa_value ?? ""}
                />
              </label>

              <label className="form-field">
                <span className="form-field__label">GPA scale</span>
                <input
                  className="text-input"
                  min="1"
                  name="gpa_scale"
                  onChange={(event) => handleChange("gpa_scale", event.target.value)}
                  required
                  step="0.1"
                  type="number"
                  value={form.gpa_scale}
                />
              </label>

              <label className="form-field">
                <span className="form-field__label">Language test type</span>
                <input
                  className="text-input"
                  name="language_test_type"
                  onChange={(event) =>
                    handleChange("language_test_type", event.target.value)
                  }
                  value={form.language_test_type ?? ""}
                />
              </label>

              <label className="form-field">
                <span className="form-field__label">Language test score</span>
                <input
                  className="text-input"
                  min="0"
                  name="language_test_score"
                  onChange={(event) =>
                    handleChange("language_test_score", event.target.value)
                  }
                  step="0.1"
                  type="number"
                  value={form.language_test_score ?? ""}
                />
              </label>
            </div>

            <div className="dashboard-actions">
              <button
                className="auth-link auth-link--primary"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting ? "Saving profile" : "Save profile and continue"}
              </button>
            </div>
          </form>
        )}
      </section>
    </AppShell>
  );
}
