"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, FeedbackNotice } from "@/components/ui/feedback-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  DocumentDetail,
  DocumentGroundingEntry,
  DocumentInputMethod,
  DocumentListResponse,
  DocumentSubmissionResponse,
  DocumentType,
} from "@/lib/types";

type DocumentState = {
  isLoading: boolean;
  isSubmitting: boolean;
  isRefreshing: boolean;
  error: string | null;
  items: DocumentDetail[];
  selectedId: string | null;
  notice: string | null;
};

type NormalizedContextItem = {
  key: string;
  primary: string;
  secondary: string | null;
  meta: string | null;
};

export function DocumentAssistanceShell() {
  const { accessToken } = useAuth();
  const [inputMethod, setInputMethod] = useState<DocumentInputMethod>("text");
  const [documentType, setDocumentType] = useState<DocumentType>("sop");
  const [title, setTitle] = useState("");
  const [scholarshipGrounding, setScholarshipGrounding] = useState("");
  const [contentText, setContentText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [state, setState] = useState<DocumentState>({
    isLoading: true,
    isSubmitting: false,
    isRefreshing: false,
    error: null,
    items: [],
    selectedId: null,
    notice: null,
  });

  useEffect(() => {
    if (!accessToken) return;

    let isActive = true;

    const loadDocuments = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const response = await apiRequest<DocumentListResponse>("/documents", {
          token: accessToken,
        });
        if (!isActive) return;

        if (response.items.length === 0) {
          setState((current) => ({
            ...current,
            isLoading: false,
            items: [],
            selectedId: null,
            notice: null,
          }));
          return;
        }

        const detailResponses = await Promise.all(
          response.items.slice(0, 6).map((item) =>
            apiRequest<DocumentDetail>(`/documents/${item.id}`, {
              token: accessToken,
            }),
          ),
        );

        if (!isActive) return;

        setState((current) => ({
          ...current,
          isLoading: false,
          items: detailResponses,
          selectedId: current.selectedId ?? detailResponses[0]?.id ?? null,
          notice: null,
        }));
      } catch (error) {
        if (!isActive) return;
        setState((current) => ({
          ...current,
          isLoading: false,
          error: resolveErrorMessage(error),
        }));
      }
    };

    void loadDocuments();

    return () => {
      isActive = false;
    };
  }, [accessToken]);

  const selectedDocument = useMemo(
    () => state.items.find((item) => item.id === state.selectedId) ?? null,
    [state.items, state.selectedId],
  );
  const [showWhyAdvice, setShowWhyAdvice] = useState(false);

  useEffect(() => {
    setShowWhyAdvice(false);
  }, [state.selectedId]);

  const groundingSelection = useMemo(
    () => parseScholarshipGrounding(scholarshipGrounding),
    [scholarshipGrounding],
  );

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    setFile(nextFile);
    setFormError(null);
  };

  const handleSubmit = async () => {
    if (!accessToken) return;

    const clientError = validateClientSubmission(
      inputMethod,
      contentText,
      file,
      groundingSelection.error,
    );
    if (clientError) {
      setFormError(clientError);
      return;
    }

    setFormError(null);
      setState((current) => ({ ...current, isSubmitting: true, error: null }));

    const formData = new FormData();
    formData.append("document_type", documentType);
    if (title.trim()) formData.append("title", title.trim());
    if (groundingSelection.ids.length === 1) {
      formData.append("scholarship_id", groundingSelection.ids[0]);
    }
    if (groundingSelection.ids.length > 1) {
      groundingSelection.ids.forEach((scholarshipId) => {
        formData.append("scholarship_ids", scholarshipId);
      });
    }
    if (inputMethod === "text") formData.append("content_text", contentText.trim());
    if (inputMethod === "file" && file) formData.append("file", file);

    try {
      const response = await apiRequest<DocumentSubmissionResponse>("/documents", {
        method: "POST",
        body: formData,
        token: accessToken,
      });

      setState((current) => {
        const nextItems = [
          response.document,
          ...current.items.filter((item) => item.id !== response.document.id),
        ];
        return {
          ...current,
          isSubmitting: false,
          items: nextItems,
          selectedId: response.document.id,
          notice: "Draft submitted. Feedback is now available in history.",
        };
      });
      setTitle("");
      setScholarshipGrounding("");
      setContentText("");
      setFile(null);
      setInputMethod("text");
      setDocumentType("sop");
    } catch (error) {
      setState((current) => ({
        ...current,
        isSubmitting: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const handleRefreshFeedback = async () => {
    if (!accessToken || !selectedDocument) return;

    setState((current) => ({ ...current, isRefreshing: true, error: null }));
    try {
      const response = await apiRequest<DocumentSubmissionResponse>(
        `/documents/${selectedDocument.id}/feedback`,
        {
          method: "POST",
          token: accessToken,
        },
      );
      setState((current) => ({
        ...current,
        isRefreshing: false,
        items: current.items.map((item) =>
          item.id === response.document.id ? response.document : item,
        ),
        selectedId: response.document.id,
        notice: "Feedback refreshed.",
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isRefreshing: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const feedback = selectedDocument?.latest_feedback ?? null;
  const generatedGuidance = getGeneratedGuidance(feedback);
  const validatedFacts = normalizeGroundingEntries(feedback?.validated_facts);
  const retrievedWritingGuidance = normalizeGroundingEntries(
    feedback?.retrieved_writing_guidance ?? feedback?.grounded_context,
  );
  const limitations = getLimitations(feedback);
  const citations = feedback?.citations ?? [];
  const groundingScore = feedback?.grounding_score ?? 0;
  const coverageFlags = feedback?.coverage_flags ?? {};
  const ungroundedWarnings = feedback?.ungrounded_warnings ?? [];
  const hasCoverageGap =
    Object.values(coverageFlags).some((covered) => !covered) ||
    ungroundedWarnings.length > 0;
  const selectedGroundingCount =
    selectedDocument?.scholarship_ids?.length ??
    (selectedDocument?.scholarship_id ? 1 : 0);

  return (
    <AppShell
      title="Get structured feedback on your application writing."
      description="Submit a draft and receive bounded, advisory writing guidance."
      eyebrow="Documents"
      intro={
        <div className="meta-row">
          <StatusBadge label="Advisory feedback" variant="generated" />
          <StatusBadge label="Facts stay separate" variant="validated" />
        </div>
      }
    >
      {state.error ? (
        <ErrorState
          testId="document-error"
          title="Document feedback is temporarily unavailable."
          description={state.error}
        />
      ) : null}

      <section className="document-grid" data-testid="document-assistance-shell">
        <article className="surface-card">
          <PageHeader
            eyebrow="Submit"
            title="Upload or paste your draft"
            description="One draft at a time for focused feedback."
          />

          <div className="toggle-row">
            <button
              className={
                inputMethod === "text"
                  ? "toggle-chip toggle-chip--active"
                  : "toggle-chip"
              }
              onClick={() => setInputMethod("text")}
              type="button"
              aria-pressed={inputMethod === "text"}
            >
              Paste text
            </button>
            <button
              className={
                inputMethod === "file"
                  ? "toggle-chip toggle-chip--active"
                  : "toggle-chip"
              }
              onClick={() => setInputMethod("file")}
              type="button"
              aria-pressed={inputMethod === "file"}
            >
              Upload file
            </button>
          </div>

          <form
            className="document-form"
            data-testid="document-submission-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleSubmit();
            }}
          >
            {state.notice ? (
              <div aria-live="polite">
                <FeedbackNotice message={state.notice} variant="success" />
              </div>
            ) : null}
            <div className="form-grid">
              <label className="form-field">
                <span className="form-field__label">Document type</span>
                <select
                  className="text-input"
                  name="document_type"
                  onChange={(event) =>
                    setDocumentType(event.target.value as DocumentType)
                  }
                  value={documentType}
                >
                  <option value="sop">Statement of purpose</option>
                  <option value="essay">Essay</option>
                </select>
              </label>

              <label className="form-field">
                <span className="form-field__label">Title</span>
                <input
                  className="text-input"
                  maxLength={255}
                  name="title"
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Fall applications draft"
                  value={title}
                />
              </label>
            </div>

            <label className="form-field">
              <span className="form-field__label">Scholarship grounding (optional)</span>
              <input
                className="text-input"
                name="scholarship_grounding"
                onChange={(event) => setScholarshipGrounding(event.target.value)}
                placeholder="Paste one scholarship ID or a few comma-separated IDs"
                value={scholarshipGrounding}
              />
              <span className="field-note">
                Use one scholarship ID or up to 3 IDs to ground feedback in
                validated scholarship facts and writing guidance.
              </span>
              {groundingSelection.ids.length > 0 ? (
                <span className="field-note">
                  Grounding {groundingSelection.ids.length} scholarship
                  {groundingSelection.ids.length === 1 ? "" : "s"} on submit.
                </span>
              ) : null}
            </label>

            {inputMethod === "text" ? (
              <label className="form-field">
                <span className="form-field__label">Draft text</span>
                <textarea
                  className="text-area"
                  name="content_text"
                  onChange={(event) => setContentText(event.target.value)}
                  placeholder="Paste your SOP or essay draft here."
                  rows={14}
                  value={contentText}
                />
                <span className="field-note">50-12,000 characters.</span>
              </label>
            ) : (
              <label className="form-field">
                <span className="form-field__label">Upload draft</span>
                <input
                  accept=".txt,.md,text/plain,text/markdown"
                  className="file-input"
                  name="file"
                  onChange={handleFileChange}
                  type="file"
                />
                <span className="field-note">UTF-8 .txt or .md under 512KB.</span>
                {file ? (
                  <span className="field-note">Selected: {file.name}</span>
                ) : null}
              </label>
            )}

            {formError ? (
              <p className="form-error" role="alert">
                {formError}
              </p>
            ) : null}

            <div className="document-actions">
              <button
                className="auth-link auth-link--primary"
                disabled={state.isSubmitting}
                type="submit"
              >
                {state.isSubmitting ? "Processing…" : "Submit for feedback"}
              </button>
            </div>
          </form>
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="History"
            title="Recent drafts"
            description="Select a draft to view its feedback."
          />
          {state.isLoading ? (
            <div className="surface-list">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : state.items.length > 0 ? (
            <div className="document-list">
              {state.items.map((item) => (
                <button
                  className={
                    item.id === state.selectedId
                      ? "document-list__item document-list__item--active"
                      : "document-list__item"
                  }
                  key={item.id}
                  onClick={() =>
                    setState((current) => ({ ...current, selectedId: item.id }))
                  }
                  type="button"
                  aria-pressed={item.id === state.selectedId}
                >
                  <div className="meta-row">
                    <StatusBadge
                      label={formatStatus(item.processing_status)}
                      variant={
                        item.processing_status === "completed"
                          ? "validated"
                          : item.processing_status === "failed"
                            ? "warning"
                            : "planned"
                      }
                    />
                    <span className="route-card__label">
                      {new Date(item.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="route-card__title">{item.title}</h3>
                  <p className="route-card__description">
                    {item.document_type.toUpperCase()} · {item.input_method}
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No drafts submitted"
              description="Upload your first statement of purpose or scholarship essay for structured feedback."
            />
          )}
        </article>
      </section>

      <section className="document-grid">
        <article className="surface-card" data-testid="document-feedback-result">
          <PageHeader
            eyebrow="Feedback"
            title="Writing guidance"
            description="Generated guidance stays separate from validated scholarship facts and retrieved writing notes."
          />
          {!selectedDocument ? (
            <EmptyState
              title="No draft selected"
              description="Submit or select a draft to see feedback here."
            />
          ) : feedback ? (
            <div className="surface-list">
              <article>
                <div className="meta-row">
                  <StatusBadge label="Generated" variant="generated" />
                  <StatusBadge
                    label={formatStatus(selectedDocument.processing_status)}
                    variant="validated"
                  />
                  {selectedGroundingCount > 0 ? (
                    <StatusBadge
                      label={
                        selectedGroundingCount === 1
                          ? "1 Scholarship Grounded"
                          : `${selectedGroundingCount} Scholarships Grounded`
                      }
                      variant="validated"
                    />
                  ) : null}
                  <StatusBadge
                    label={`Grounding score: ${Math.round(groundingScore * 100)}%`}
                    variant={groundingScore >= 0.7 ? "validated" : "warning"}
                  />
                </div>
                {hasCoverageGap ? (
                  <div className="guidance-callout" role="status" aria-live="polite">
                    <p className="list-heading">Partial grounding coverage detected</p>
                    <ul className="detail-list">
                      {ungroundedWarnings.length > 0 ? (
                        ungroundedWarnings.map((warning) => <li key={warning}>{warning}</li>)
                      ) : (
                        <li>
                          Some evidence sections are missing. Add clearer preparation and
                          scholarship-fit details for stronger guidance.
                        </li>
                      )}
                    </ul>
                  </div>
                ) : null}
                <p className="list-heading">Generated guidance</p>
                <p className="body-copy">{generatedGuidance.summary}</p>
              </article>
              <article>
                <p className="list-heading">Strengths</p>
                <ul className="detail-list">
                  {generatedGuidance.strengths.map((item, index) => (
                    <li key={item}>
                      {item}
                      {renderCitationMarker(index, citations.length)}
                    </li>
                  ))}
                </ul>
              </article>
              <article>
                <p className="list-heading">Revision priorities</p>
                <ul className="detail-list">
                  {generatedGuidance.revision_priorities.map((item, index) => (
                    <li key={item}>
                      {item}
                      {renderCitationMarker(index, citations.length)}
                    </li>
                  ))}
                </ul>
              </article>
              <article>
                <p className="list-heading">Cautions</p>
                <ul className="detail-list">
                  {generatedGuidance.caution_notes.map((item, index) => (
                    <li key={item}>
                      {item}
                      {renderCitationMarker(index, citations.length)}
                    </li>
                  ))}
                </ul>
              </article>
              {citations.length > 0 ? (
                <article>
                  <div className="meta-row">
                    <p className="list-heading">Why this advice</p>
                    <button
                      className="nav-link text-xs"
                      type="button"
                      onClick={() => setShowWhyAdvice((current) => !current)}
                    >
                      {showWhyAdvice ? "Hide details" : "Show details"}
                    </button>
                  </div>
                  {showWhyAdvice ? (
                    <ul className="detail-list">
                      {citations.map((citation, index) => (
                        <li key={`${citation.source_id}-${index}`}>
                          <strong>[{index + 1}] {citation.title}</strong>: {citation.snippet}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </article>
              ) : null}
              <div className="document-actions">
                <button
                  className="auth-link auth-link--secondary"
                  disabled={state.isRefreshing}
                  onClick={() => void handleRefreshFeedback()}
                  type="button"
                  aria-busy={state.isRefreshing}
                >
                  {state.isRefreshing ? "Refreshing…" : "Refresh feedback"}
                </button>
              </div>
            </div>
          ) : (
            <EmptyState
              title="Analyzing draft"
              description="Feedback is currently being generated. Check back shortly."
            />
          )}
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Context"
            title="About this feedback"
            description="Validated scholarship facts, retrieved writing guidance, and limitations are displayed separately."
          />
          {feedback ? (
            <div className="surface-list">
              <article>
                <p className="list-heading">Validated facts</p>
                {validatedFacts.length > 0 ? (
                  <ul className="detail-list">
                    {validatedFacts.map((item) => (
                      <li key={item.key}>
                        {item.primary}
                        {item.secondary ? <span> {item.secondary}</span> : null}
                        {item.meta ? <span> ({item.meta})</span> : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="body-copy">
                    No validated scholarship facts were attached to this feedback.
                  </p>
                )}
              </article>
              <article>
                <p className="list-heading">Retrieved writing guidance</p>
                {retrievedWritingGuidance.length > 0 ? (
                  <ul className="detail-list">
                    {retrievedWritingGuidance.map((item) => (
                      <li key={item.key}>
                        {item.primary}
                        {item.secondary ? <span> {item.secondary}</span> : null}
                        {item.meta ? <span> ({item.meta})</span> : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="body-copy">
                    No retrieved writing guidance was returned for this draft.
                  </p>
                )}
              </article>
              <article className="guidance-callout">
                <p className="list-heading">Limitations</p>
                <ul className="detail-list">
                  {limitations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              {citations.length > 0 ? (
                <article>
                  <p className="list-heading">Citations</p>
                  <ul className="detail-list">
                    {citations.map((item) => (
                      <li key={`${item.source_id}-${item.url_or_ref}`}>
                        <strong>{item.title}</strong> - {item.url_or_ref}
                      </li>
                    ))}
                  </ul>
                </article>
              ) : null}
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Context will appear after the first feedback response.
              </p>
            </div>
          )}
        </article>
      </section>
    </AppShell>
  );
}

function renderCitationMarker(index: number, citationCount: number) {
  if (citationCount === 0) {
    return null;
  }
  const marker = (index % citationCount) + 1;
  return <sup aria-label={`Citation ${marker}`}> [{marker}]</sup>;
}

function validateClientSubmission(
  inputMethod: DocumentInputMethod,
  contentText: string,
  file: File | null,
  groundingError: string | null,
) {
  if (groundingError) {
    return groundingError;
  }

  if (inputMethod === "text") {
    if (contentText.trim().length < 50) {
      return "Paste at least 50 characters before requesting feedback.";
    }
    return null;
  }

  if (!file) {
    return "Select a .txt or .md file before requesting feedback.";
  }

  return null;
}

function formatStatus(status: string) {
  if (status === "completed") return "Feedback ready";
  if (status === "processing") return "Processing";
  if (status === "failed") return "Needs retry";
  return "Submitted";
}

function resolveErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "message" in error) {
    return (error as ApiError).message;
  }
  return "Unexpected document assistance failure";
}

function parseScholarshipGrounding(value: string) {
  const ids = value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
  const uniqueIds = Array.from(new Set(ids));

  if (uniqueIds.length > 3) {
    return {
      ids: uniqueIds,
      error: "Grounding supports up to 3 scholarship IDs per submission.",
    };
  }

  return {
    ids: uniqueIds,
    error: null,
  };
}

function getGeneratedGuidance(feedback: DocumentDetail["latest_feedback"]) {
  if (!feedback) {
    return {
      summary: "",
      strengths: [] as string[],
      revision_priorities: [] as string[],
      caution_notes: [] as string[],
    };
  }

  return {
    summary: feedback.generated_guidance?.summary ?? feedback.summary,
    strengths: feedback.generated_guidance?.strengths ?? feedback.strengths,
    revision_priorities:
      feedback.generated_guidance?.revision_priorities ??
      feedback.revision_priorities,
    caution_notes:
      feedback.generated_guidance?.caution_notes ?? feedback.caution_notes,
  };
}

function getLimitations(feedback: DocumentDetail["latest_feedback"]) {
  if (!feedback) {
    return [];
  }

  if (feedback.limitations && feedback.limitations.length > 0) {
    return feedback.limitations;
  }

  return feedback.limitation_notice ? [feedback.limitation_notice] : [];
}

function normalizeGroundingEntries(
  entries?: DocumentGroundingEntry[] | null,
): NormalizedContextItem[] {
  if (!entries || entries.length === 0) {
    return [];
  }

  return entries.map((entry, index) => {
    if (typeof entry === "string") {
      return {
        key: `${index}-${entry}`,
        primary: entry,
        secondary: null,
        meta: null,
      };
    }

    const label = entry.label?.trim() ?? "";
    const detail = entry.detail?.trim() ?? "";
    const value = entry.value?.trim() ?? "";
    const citation = entry.citation?.trim() ?? "";
    const primary = label || detail || value || citation || "Context item";
    const secondary = label && detail ? detail : value || null;
    const meta = [entry.source, entry.scholarship_id, citation]
      .filter((item): item is string => Boolean(item))
      .join(" · ");

    return {
      key: `${index}-${primary}-${secondary ?? ""}-${meta}`,
      primary,
      secondary,
      meta: meta || null,
    };
  });
}
