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
              ? "Your profile is already on file. You can adjust it before opening recommendations."
              : "Your current profile has been loaded for review.",
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
      ? "US scope remains limited to Fulbright-related published opportunities in this MVP."
      : "Canada is the strongest part of the current MVP corpus, so recommendations are most complete here.";
  }, [form.target_country_code]);

  const intro = useMemo(() => {
    if (mode === "onboarding") {
      return (
        <div className="surface-band">
          <div className="button-row">
            <StatusBadge label="First-run setup" variant="validated" />
            <StatusBadge label="5 essential inputs" variant="neutral" />
          </div>
          <p className="body-copy">
            This first pass asks only for the details needed to generate a clear,
            explainable shortlist.
          </p>
        </div>
      );
    }

    return (
      <div className="surface-band">
        <div className="button-row">
          <StatusBadge label="Editable profile" variant="neutral" />
          <StatusBadge label="Recommendation input" variant="generated" />
        </div>
        <p className="body-copy">
          Keep this profile current when your target country, field, or academic
          standing changes.
        </p>
      </div>
    );
  }, [mode]);

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
      eyebrow={mode === "onboarding" ? "Onboarding" : "Profile"}
      title={
        mode === "onboarding"
          ? "Set the essentials once so ScholarAI can explain why an opportunity fits."
          : "Keep the profile behind your recommendations clear, current, and easy to inspect."
      }
      description={
        mode === "onboarding"
          ? "The MVP starts with a short profile instead of a long intake. Each field is here because it affects discovery or eligibility."
          : "This workspace keeps the recommendation contract visible and editable without turning profile setup into a complex account flow."
      }
      intro={intro}
    >
      <section className="page-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow={mode === "onboarding" ? "Why these fields matter" : "Profile posture"}
            title={
              mode === "onboarding"
                ? "A small amount of information can still produce a trustworthy shortlist."
                : "Recommendations stay readable when the input stays disciplined."
            }
            description={
              mode === "onboarding"
                ? "ScholarAI needs academic intent, destination, and a few eligibility anchors. Everything else is deferred until the product earns it."
                : "The current MVP uses citizenship, academic intent, GPA, and optional language evidence to rank only published opportunities."
            }
          />
          <div className="surface-list">
            <article>
              <p className="list-heading">Recommendation anchors</p>
              <p className="body-copy">
                Citizenship, target country, target field, and GPA keep the shortlist
                grounded in explicit user inputs instead of hidden assumptions.
              </p>
            </article>
            <article>
              <p className="list-heading">Scope discipline</p>
              <p className="body-copy">
                The current dataset focuses on Canada-first MS opportunities with
                only limited Fulbright-related US coverage.
              </p>
            </article>
          </div>
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Readiness note"
            title="What happens after this"
            description="Saving the profile takes you directly into the recommendation workspace so the result stays connected to the inputs you just reviewed."
            compact
          />
          <div className="surface-list">
            <article>
              <div className="meta-row">
                <StatusBadge label="Published data only" variant="validated" />
                <StatusBadge label="Rules-first ranking" variant="generated" />
              </div>
              <p className="body-copy">{helperNote}</p>
            </article>
            {message ? (
              <article>
                <p className="list-heading">Status</p>
                <p className="body-copy">{message}</p>
              </article>
            ) : null}
            {error ? (
              <article>
                <p className="list-heading">Attention needed</p>
                <p className="form-error">{error}</p>
              </article>
            ) : null}
          </div>
        </article>
      </section>

      <section className="surface-card" data-testid="profile-form-shell">
        <PageHeader
          eyebrow={mode === "onboarding" ? "Step 1 of 1" : "Profile editor"}
          title={
            mode === "onboarding"
              ? "Save the minimum profile needed for your first shortlist."
              : "Review and update the information ScholarAI uses for ranking."
          }
          description="The form is grouped by user intent so it feels like planning, not raw data entry."
        />
        {isLoading ? (
          <p className="body-copy">Loading your saved profile.</p>
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
              <p className="route-card__label">Eligibility anchors</p>
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
              </div>
            </section>

            <section className="form-section">
              <p className="route-card__label">Optional language evidence</p>
              <div className="form-grid">
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
            </section>

            <div className="dashboard-actions">
              <button
                className="auth-link auth-link--primary"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting
                  ? "Saving profile"
                  : mode === "onboarding"
                    ? "Save and open recommendations"
                    : "Save profile"}
              </button>
            </div>
          </form>
        )}
      </section>
    </AppShell>
  );
}
