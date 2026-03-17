"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
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

type ProfileFormShellProps = {
  mode?: "onboarding" | "profile";
};

export function ProfileFormShell({
  mode = "profile",
}: ProfileFormShellProps) {
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
            mode === "onboarding"
              ? "Your profile is already on file. Adjust anything before continuing."
              : "Profile loaded. Make changes and save when ready.",
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
  }, [accessToken, mode]);

  const helperNote = useMemo(() => {
    return form.target_country_code === "US"
      ? "US coverage is limited to Fulbright-related opportunities."
      : "Canada has the strongest coverage in the current catalog.";
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
      setMessage("Profile saved. Opening recommendations.");
      router.push("/recommendations");
    } catch (caught) {
      setError((caught as ApiError).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell
      eyebrow={mode === "onboarding" ? "Get started" : "Profile"}
      title={
        mode === "onboarding"
          ? "Tell us the essentials so we can find scholarships that fit."
          : "Keep your profile current for better recommendations."
      }
      description={
        mode === "onboarding"
          ? "Five fields are all we need to build your first personalized shortlist."
          : "Changes here update how scholarships are ranked and explained."
      }
      intro={
        <div className="meta-row">
          <StatusBadge
            label={mode === "onboarding" ? "First-run setup" : "Editable profile"}
            variant={mode === "onboarding" ? "validated" : "neutral"}
          />
          <span className="body-copy">{helperNote}</span>
        </div>
      }
    >
      {message ? (
        <section className="info-band">
          <p className="body-copy">{message}</p>
        </section>
      ) : null}

      {error ? (
        <section className="surface-card">
          <p className="form-error">{error}</p>
        </section>
      ) : null}

      <section className="surface-card" data-testid="profile-form-shell">
        {isLoading ? (
          <p className="body-copy">Loading your profile…</p>
        ) : (
          <form
            className="profile-form"
            data-testid="profile-form"
            onSubmit={handleSubmit}
          >
            <section className="form-section">
              <p className="route-card__label">Academic direction</p>
              <div className="form-grid">
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
              </div>
            </section>

            <section className="form-section">
              <p className="route-card__label">Eligibility</p>
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
                  <span className="form-field__label">GPA</span>
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
              </div>
            </section>

            <section className="form-section">
              <p className="route-card__label">Language (optional)</p>
              <div className="form-grid">
                <label className="form-field">
                  <span className="form-field__label">Test type</span>
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
                  <span className="form-field__label">Score</span>
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
            </section>

            <div className="dashboard-actions">
              <button
                className="auth-link auth-link--primary"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting
                  ? "Saving…"
                  : mode === "onboarding"
                    ? "Save and view recommendations"
                    : "Save profile"}
              </button>
            </div>
          </form>
        )}
      </section>
    </AppShell>
  );
}
