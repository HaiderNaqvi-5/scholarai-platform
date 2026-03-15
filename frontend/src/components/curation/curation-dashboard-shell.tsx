"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  CurationRecordDetail,
  CurationRecordListResponse,
  CurationRecordState,
} from "@/lib/types";

const FILTERS: CurationRecordState[] = [
  "raw",
  "validated",
  "published",
  "archived",
];

type CurationState = {
  isLoading: boolean;
  isDetailLoading: boolean;
  isSaving: boolean;
  error: string | null;
  filter: CurationRecordState;
  records: CurationRecordListResponse["items"];
  selectedRecord: CurationRecordDetail | null;
};

type EditState = {
  title: string;
  provider_name: string;
  country_code: string;
  summary: string;
  funding_summary: string;
  field_tags: string;
  degree_levels: string;
  citizenship_rules: string;
  min_gpa_value: string;
  review_notes: string;
};

const EMPTY_EDIT_STATE: EditState = {
  title: "",
  provider_name: "",
  country_code: "",
  summary: "",
  funding_summary: "",
  field_tags: "",
  degree_levels: "",
  citizenship_rules: "",
  min_gpa_value: "",
  review_notes: "",
};

export function CurationDashboardShell() {
  const { accessToken } = useAuth();
  const [state, setState] = useState<CurationState>({
    isLoading: true,
    isDetailLoading: false,
    isSaving: false,
    error: null,
    filter: "raw",
    records: [],
    selectedRecord: null,
  });
  const [editState, setEditState] = useState<EditState>(EMPTY_EDIT_STATE);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let isActive = true;

    const loadRecords = async () => {
      setState((current) => ({
        ...current,
        isLoading: true,
        error: null,
        selectedRecord: null,
      }));

      try {
        const response = await apiRequest<CurationRecordListResponse>(
          `/curation/records?state=${state.filter}`,
          { token: accessToken },
        );
        if (!isActive) {
          return;
        }

        setState((current) => ({
          ...current,
          isLoading: false,
          records: response.items,
        }));

        if (response.items[0]) {
          void loadRecordDetail(response.items[0].record_id, true);
        }
      } catch (error) {
        if (!isActive) {
          return;
        }
        setState((current) => ({
          ...current,
          isLoading: false,
          records: [],
          error: resolveErrorMessage(error),
        }));
      }
    };

    const loadRecordDetail = async (recordId: string, initial = false) => {
      setState((current) => ({
        ...current,
        isDetailLoading: !initial,
        error: null,
      }));
      try {
        const detail = await apiRequest<CurationRecordDetail>(
          `/curation/records/${recordId}`,
          { token: accessToken },
        );
        if (!isActive) {
          return;
        }
        setState((current) => ({
          ...current,
          isDetailLoading: false,
          selectedRecord: detail,
        }));
        setEditState(buildEditState(detail));
      } catch (error) {
        if (!isActive) {
          return;
        }
        setState((current) => ({
          ...current,
          isDetailLoading: false,
          error: resolveErrorMessage(error),
        }));
      }
    };

    void loadRecords();

    return () => {
      isActive = false;
    };
  }, [accessToken, state.filter]);

  const selectedId = state.selectedRecord?.record_id ?? null;

  const actionButtons = useMemo(() => {
    if (!state.selectedRecord) {
      return [];
    }

    if (state.selectedRecord.record_state === "raw") {
      return [
        { label: "Approve", action: "approve", variant: "auth-link--primary" },
        { label: "Reject", action: "reject", variant: "auth-link--secondary" },
      ];
    }

    if (state.selectedRecord.record_state === "validated") {
      return [
        { label: "Publish", action: "publish", variant: "auth-link--primary" },
        { label: "Reject", action: "reject", variant: "auth-link--secondary" },
      ];
    }

    if (state.selectedRecord.record_state === "published") {
      return [
        { label: "Unpublish", action: "unpublish", variant: "auth-link--secondary" },
      ];
    }

    return [];
  }, [state.selectedRecord]);

  const refreshCurrentFilter = async (targetRecordId?: string) => {
    if (!accessToken) {
      return;
    }

    setState((current) => ({ ...current, isLoading: true, error: null }));
    try {
      const response = await apiRequest<CurationRecordListResponse>(
        `/curation/records?state=${state.filter}`,
        { token: accessToken },
      );
      setState((current) => ({
        ...current,
        isLoading: false,
        records: response.items,
      }));

      const nextRecordId = targetRecordId ?? response.items[0]?.record_id;
      if (nextRecordId) {
        const detail = await apiRequest<CurationRecordDetail>(
          `/curation/records/${nextRecordId}`,
          { token: accessToken },
        );
        setState((current) => ({
          ...current,
          selectedRecord: detail,
          isDetailLoading: false,
        }));
        setEditState(buildEditState(detail));
      } else {
        setState((current) => ({ ...current, selectedRecord: null }));
        setEditState(EMPTY_EDIT_STATE);
      }
    } catch (error) {
      setState((current) => ({
        ...current,
        isLoading: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const loadRecord = async (recordId: string) => {
    if (!accessToken) {
      return;
    }

    setState((current) => ({ ...current, isDetailLoading: true, error: null }));
    try {
      const detail = await apiRequest<CurationRecordDetail>(`/curation/records/${recordId}`, {
        token: accessToken,
      });
      setState((current) => ({
        ...current,
        isDetailLoading: false,
        selectedRecord: detail,
      }));
      setEditState(buildEditState(detail));
    } catch (error) {
      setState((current) => ({
        ...current,
        isDetailLoading: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const saveCorrections = async () => {
    if (!accessToken || !state.selectedRecord) {
      return;
    }

    setState((current) => ({ ...current, isSaving: true, error: null }));
    try {
      const detail = await apiRequest<CurationRecordDetail>(
        `/curation/records/${state.selectedRecord.record_id}`,
        {
          method: "PATCH",
          token: accessToken,
          body: JSON.stringify({
            title: editState.title,
            provider_name: emptyToNull(editState.provider_name),
            country_code: editState.country_code.toUpperCase(),
            summary: emptyToNull(editState.summary),
            funding_summary: emptyToNull(editState.funding_summary),
            field_tags: parseCsv(editState.field_tags),
            degree_levels: parseCsv(editState.degree_levels),
            citizenship_rules: parseCsv(editState.citizenship_rules),
            min_gpa_value: editState.min_gpa_value
              ? Number(editState.min_gpa_value)
              : null,
            review_notes: emptyToNull(editState.review_notes),
          }),
        },
      );
      setState((current) => ({
        ...current,
        isSaving: false,
        selectedRecord: detail,
        records: current.records.map((item) =>
          item.record_id === detail.record_id ? detail : item,
        ),
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const runAction = async (
    action: "approve" | "reject" | "publish" | "unpublish",
  ) => {
    if (!accessToken || !state.selectedRecord) {
      return;
    }

    setState((current) => ({ ...current, isSaving: true, error: null }));
    try {
      await apiRequest<CurationRecordDetail>(
        `/curation/records/${state.selectedRecord.record_id}/${action}`,
        {
          method: "POST",
          token: accessToken,
          body: JSON.stringify({ note: emptyToNull(editState.review_notes) }),
        },
      );
      setState((current) => ({ ...current, isSaving: false }));
      await refreshCurrentFilter();
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  return (
    <AppShell
      title="Curator review keeps raw records internal, validated records traceable, and published records intentional."
      description="This slice adds the minimum protected curation workflow for review, correction, approval, rejection, publication, and unpublication."
      eyebrow="Curator workspace"
    >
      <section className="curation-hero" data-testid="curation-dashboard-shell">
        <div>
          <p className="section-eyebrow">Curation posture</p>
          <h2 className="section-title">
            Raw data stays internal until a curator reviews and promotes it.
          </h2>
          <p className="body-copy">
            Published scholarship records remain the only user-facing state.
            This dashboard is intentionally operational, narrow, and traceable.
          </p>
        </div>
        <div className="curation-hero__badges">
          <StatusBadge label="Admin only" variant="validated" />
          <StatusBadge label="Published is user-facing" variant="generated" />
        </div>
      </section>

      {state.error ? (
        <section className="surface-card" data-testid="curation-error">
          <p className="section-eyebrow">Curation error</p>
          <h2 className="section-title">The review workspace needs attention.</h2>
          <p className="body-copy">{state.error}</p>
        </section>
      ) : null}

      <section className="curation-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="Record states"
            title="Filter by explicit lifecycle stage"
            description="The workflow remains simple: raw, validated, published, or archived."
          />
          <div className="toggle-row">
            {FILTERS.map((filter) => (
              <button
                className={
                  state.filter === filter
                    ? "toggle-chip toggle-chip--active"
                    : "toggle-chip"
                }
                key={filter}
                onClick={() =>
                  setState((current) => ({
                    ...current,
                    filter,
                    selectedRecord: null,
                  }))
                }
                type="button"
              >
                {filter}
              </button>
            ))}
          </div>
          {state.isLoading ? (
            <p className="body-copy">Loading curation records.</p>
          ) : state.records.length > 0 ? (
            <div className="curation-list">
              {state.records.map((record) => (
                <button
                  className={
                    record.record_id === selectedId
                      ? "curation-list__item curation-list__item--active"
                      : "curation-list__item"
                  }
                  data-testid={`curation-record-${record.record_state}`}
                  key={record.record_id}
                  onClick={() => void loadRecord(record.record_id)}
                  type="button"
                >
                  <div className="meta-row">
                    <StatusBadge
                      label={record.record_state}
                      variant={badgeVariant(record.record_state)}
                    />
                    <span className="route-card__label">{record.country_code}</span>
                  </div>
                  <h3 className="route-card__title">{record.title}</h3>
                  <p className="route-card__description">
                    {record.provider_name ?? "Provider not listed"}
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                No records are in the `{state.filter}` state right now.
              </p>
            </div>
          )}
        </article>

        <article className="surface-panel" data-testid="curation-record-detail">
          <PageHeader
            eyebrow="Record review"
            title="Inspect and correct one record at a time"
            description="The internal review view focuses on provenance, canonical fields, and explicit state changes."
          />
          {state.isDetailLoading ? (
            <p className="body-copy">Loading selected record.</p>
          ) : state.selectedRecord ? (
            <div className="surface-list">
              <article>
                <div className="meta-row">
                  <StatusBadge
                    label={state.selectedRecord.record_state}
                    variant={badgeVariant(state.selectedRecord.record_state)}
                  />
                  <span className="route-card__label">
                    Source type {state.selectedRecord.source_type ?? "unknown"}
                  </span>
                </div>
                <p className="body-copy">{state.selectedRecord.source_url}</p>
              </article>
              <div className="form-grid">
                <label className="form-field">
                  <span className="form-field__label">Title</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({ ...current, title: event.target.value }))
                    }
                    value={editState.title}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Provider</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        provider_name: event.target.value,
                      }))
                    }
                    value={editState.provider_name}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Country</span>
                  <input
                    className="text-input"
                    maxLength={2}
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        country_code: event.target.value,
                      }))
                    }
                    value={editState.country_code}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Minimum GPA</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        min_gpa_value: event.target.value,
                      }))
                    }
                    value={editState.min_gpa_value}
                  />
                </label>
              </div>
              <label className="form-field">
                <span className="form-field__label">Summary</span>
                <textarea
                  className="text-area"
                  onChange={(event) =>
                    setEditState((current) => ({ ...current, summary: event.target.value }))
                  }
                  rows={6}
                  value={editState.summary}
                />
              </label>
              <div className="form-grid">
                <label className="form-field">
                  <span className="form-field__label">Field tags</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({ ...current, field_tags: event.target.value }))
                    }
                    placeholder="data science, analytics"
                    value={editState.field_tags}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Degree levels</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        degree_levels: event.target.value,
                      }))
                    }
                    placeholder="MS"
                    value={editState.degree_levels}
                  />
                </label>
              </div>
              <label className="form-field">
                <span className="form-field__label">Citizenship rules</span>
                <input
                  className="text-input"
                  onChange={(event) =>
                    setEditState((current) => ({
                      ...current,
                      citizenship_rules: event.target.value,
                    }))
                  }
                  placeholder="PK, IN"
                  value={editState.citizenship_rules}
                />
              </label>
              <label className="form-field">
                <span className="form-field__label">Reviewer notes</span>
                <textarea
                  className="text-area"
                  data-testid="curation-review-notes"
                  onChange={(event) =>
                    setEditState((current) => ({
                      ...current,
                      review_notes: event.target.value,
                    }))
                  }
                  rows={4}
                  value={editState.review_notes}
                />
              </label>
              <div className="document-actions">
                <button
                  className="auth-link auth-link--secondary"
                  data-testid="curation-save"
                  disabled={state.isSaving}
                  onClick={() => void saveCorrections()}
                  type="button"
                >
                  {state.isSaving ? "Saving" : "Save corrections"}
                </button>
                {actionButtons.map((item) => (
                  <button
                    className={`auth-link ${item.variant}`}
                    data-testid={`curation-${item.action}`}
                    disabled={state.isSaving}
                    key={item.action}
                    onClick={() =>
                      void runAction(
                        item.action as "approve" | "reject" | "publish" | "unpublish",
                      )
                    }
                    type="button"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Select a record from the list to review it.
              </p>
            </div>
          )}
        </article>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Traceability"
          title="Why this workflow stays narrow"
          description="The MVP focuses on state enforcement, provenance, and publish control rather than analytics-heavy admin tooling."
        />
        <div className="split-panel">
          <article className="data-callout">
            <p className="list-label">Source-of-truth rule</p>
            <p className="body-copy">
              Raw records stay internal. Only published records should reach
              discovery, recommendations, and saved-opportunity flows.
            </p>
          </article>
          <article className="guidance-callout">
            <p className="list-label">Curator responsibility</p>
            <p className="body-copy">
              Review notes, explicit state changes, and audit entries provide
              the minimum traceability needed for MVP governance.
            </p>
          </article>
        </div>
      </section>
    </AppShell>
  );
}

function buildEditState(record: CurationRecordDetail): EditState {
  return {
    title: record.title,
    provider_name: record.provider_name ?? "",
    country_code: record.country_code,
    summary: record.summary ?? "",
    funding_summary: record.funding_summary ?? "",
    field_tags: record.field_tags.join(", "),
    degree_levels: record.degree_levels.join(", "),
    citizenship_rules: record.citizenship_rules.join(", "),
    min_gpa_value: record.min_gpa_value?.toString() ?? "",
    review_notes: record.review_notes ?? "",
  };
}

function parseCsv(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function emptyToNull(value: string) {
  const normalized = value.trim();
  return normalized ? normalized : null;
}

function badgeVariant(state: CurationRecordState) {
  if (state === "published") {
    return "validated";
  }
  if (state === "validated") {
    return "generated";
  }
  if (state === "archived") {
    return "warning";
  }
  return "planned";
}

function resolveErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "message" in error) {
    return (error as ApiError).message;
  }
  return "Unexpected curation failure";
}
