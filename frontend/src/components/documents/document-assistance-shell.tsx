"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  DocumentDetail,
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
};

export function DocumentAssistanceShell() {
  const { accessToken } = useAuth();
  const [inputMethod, setInputMethod] = useState<DocumentInputMethod>("text");
  const [documentType, setDocumentType] = useState<DocumentType>("sop");
  const [title, setTitle] = useState("");
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
  });

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let isActive = true;

    const loadDocuments = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const response = await apiRequest<DocumentListResponse>("/documents", {
          token: accessToken,
        });
        if (!isActive) {
          return;
        }

        if (response.items.length === 0) {
          setState((current) => ({
            ...current,
            isLoading: false,
            items: [],
            selectedId: null,
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

        if (!isActive) {
          return;
        }

        setState((current) => ({
          ...current,
          isLoading: false,
          items: detailResponses,
          selectedId: current.selectedId ?? detailResponses[0]?.id ?? null,
        }));
      } catch (error) {
        if (!isActive) {
          return;
        }
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

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    setFile(nextFile);
    setFormError(null);
  };

  const handleSubmit = async () => {
    if (!accessToken) {
      return;
    }

    const clientError = validateClientSubmission(inputMethod, contentText, file);
    if (clientError) {
      setFormError(clientError);
      return;
    }

    setFormError(null);
    setState((current) => ({ ...current, isSubmitting: true, error: null }));

    const formData = new FormData();
    formData.append("document_type", documentType);
    if (title.trim()) {
      formData.append("title", title.trim());
    }
    if (inputMethod === "text") {
      formData.append("content_text", contentText.trim());
    }
    if (inputMethod === "file" && file) {
      formData.append("file", file);
    }

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
        };
      });
      setTitle("");
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
    if (!accessToken || !selectedDocument) {
      return;
    }

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
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isRefreshing: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  return (
    <AppShell
      title="Work on one application draft at a time with grounded, clearly bounded feedback."
      description="Document assistance is designed as a disciplined writing workspace, not a general-purpose AI editor."
      eyebrow="Document assistance"
      intro={
        <div className="surface-band">
          <div className="button-row">
            <StatusBadge label="Generated guidance" variant="generated" />
            <StatusBadge label="Facts stay separate" variant="validated" />
          </div>
          <p className="body-copy">
            Writing feedback is advisory. Official scholarship requirements still belong to published scholarship records.
          </p>
        </div>
      }
    >
      <section className="document-hero" data-testid="document-assistance-shell">
        <div>
          <p className="section-eyebrow">Writing workspace</p>
          <h2 className="section-title">
            Submit a focused draft, review one structured response, and keep the reasoning visible.
          </h2>
          <p className="body-copy">
            Generated feedback remains advisory. Official scholarship rules,
            deadlines, and eligibility constraints still come from validated
            scholarship records elsewhere in the product.
          </p>
        </div>
        <div className="document-hero__badges">
          <StatusBadge label="Generated guidance" variant="generated" />
          <StatusBadge label="Validated facts stay separate" variant="validated" />
        </div>
      </section>

      {state.error ? (
        <section className="surface-card" data-testid="document-error">
          <p className="section-eyebrow">Document assistance error</p>
          <h2 className="section-title">The document flow needs attention.</h2>
          <p className="body-copy">{state.error}</p>
        </section>
      ) : null}

      <section className="document-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="Submit draft"
            title="Paste text or upload a plain-text draft"
            description="The MVP keeps input narrow on purpose so the feedback remains easy to understand and review."
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
                <span className="form-field__label">Draft title</span>
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

            {inputMethod === "text" ? (
              <label className="form-field">
                <span className="form-field__label">Document text</span>
                <textarea
                  className="text-area"
                  name="content_text"
                  onChange={(event) => setContentText(event.target.value)}
                  placeholder="Paste your SOP or essay draft here. Keep it to one focused draft for the MVP flow."
                  rows={14}
                  value={contentText}
                />
                <span className="field-note">
                  Minimum 50 characters. Maximum 12,000 characters.
                </span>
              </label>
            ) : (
              <label className="form-field">
                <span className="form-field__label">Upload plain-text draft</span>
                <input
                  accept=".txt,.md,text/plain,text/markdown"
                  className="file-input"
                  name="file"
                  onChange={handleFileChange}
                  type="file"
                />
                <span className="field-note">
                  Use UTF-8 `.txt` or `.md` files under 512KB.
                </span>
                {file ? (
                  <span className="field-note">Selected file: {file.name}</span>
                ) : null}
              </label>
            )}

            {formError ? <p className="form-error">{formError}</p> : null}

            <div className="document-actions">
              <button
                className="auth-link auth-link--primary"
                disabled={state.isSubmitting}
                type="submit"
              >
                {state.isSubmitting ? "Processing draft" : "Submit for feedback"}
              </button>
              <p className="field-note">
                Feedback is generated from your draft and a bounded writing checklist.
              </p>
            </div>
          </form>
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Recent drafts"
            title="Recent draft history"
            description="This is a focused working set for active drafts, not a full document archive."
          />
          {state.isLoading ? (
            <p className="body-copy">Loading recent document records.</p>
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
                    {item.document_type.toUpperCase()} · {item.input_method} input
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                No drafts have been submitted yet. Start with one SOP or essay
                draft to open the feedback panel.
              </p>
            </div>
          )}
        </article>
      </section>

      <section className="document-grid">
        <article className="surface-card" data-testid="document-feedback-result">
          <PageHeader
            eyebrow="Feedback result"
            title="Structured writing guidance"
            description="Feedback is grouped so you can separate revision advice from scholarship facts that live elsewhere."
          />
          {!selectedDocument ? (
            <div className="empty-panel">
              <p className="body-copy">
                Submit a draft to populate the feedback view.
              </p>
            </div>
          ) : selectedDocument.latest_feedback ? (
            <div className="surface-list">
              <article>
                <div className="meta-row">
                  <StatusBadge label="Generated guidance" variant="generated" />
                  <StatusBadge
                    label={formatStatus(selectedDocument.processing_status)}
                    variant="validated"
                  />
                </div>
                <p className="body-copy">{selectedDocument.latest_feedback.summary}</p>
              </article>
              <article>
                <p className="list-heading">Strengths</p>
                <ul className="detail-list">
                  {selectedDocument.latest_feedback.strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article>
                <p className="list-heading">Revision priorities</p>
                <ul className="detail-list">
                  {selectedDocument.latest_feedback.revision_priorities.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article>
                <p className="list-heading">Caution notes</p>
                <ul className="detail-list">
                  {selectedDocument.latest_feedback.caution_notes.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <div className="document-actions">
                <button
                  className="auth-link auth-link--secondary"
                  disabled={state.isRefreshing}
                  onClick={() => void handleRefreshFeedback()}
                  type="button"
                >
                  {state.isRefreshing ? "Refreshing feedback" : "Refresh feedback"}
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Feedback is not ready yet for this draft.
              </p>
            </div>
          )}
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Grounding and limits"
            title="Why the feedback stays bounded"
            description="ScholarAI is explicit about where writing guidance ends and official scholarship information begins."
          />
          {selectedDocument?.latest_feedback ? (
            <div className="surface-list">
              <article>
                <p className="list-heading">Grounded context</p>
                <ul className="detail-list">
                  {selectedDocument.latest_feedback.grounded_context.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article>
                <p className="list-heading">Citations</p>
                <ul className="detail-list">
                  {selectedDocument.latest_feedback.citations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="guidance-callout">
                <p className="list-heading">Limitation notice</p>
                <p className="body-copy">
                  {selectedDocument.latest_feedback.limitation_notice}
                </p>
              </article>
              <article className="data-callout">
                <p className="list-heading">Validated facts remain elsewhere</p>
                <p className="body-copy">
                  Use published scholarship records for official requirements,
                  deadlines, and eligibility logic. This panel does not replace
                  those sources.
                </p>
              </article>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                The limits panel will populate after the first successful
                feedback response.
              </p>
            </div>
          )}
        </article>
      </section>
    </AppShell>
  );
}

function validateClientSubmission(
  inputMethod: DocumentInputMethod,
  contentText: string,
  file: File | null,
) {
  if (inputMethod === "text") {
    if (contentText.trim().length < 50) {
      return "Paste at least 50 characters before requesting feedback.";
    }
    return null;
  }

  if (!file) {
    return "Select a `.txt` or `.md` file before requesting feedback.";
  }

  return null;
}

function formatStatus(status: string) {
  if (status === "completed") {
    return "Feedback ready";
  }
  if (status === "processing") {
    return "Processing";
  }
  if (status === "failed") {
    return "Needs retry";
  }
  return "Submitted";
}

function resolveErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "message" in error) {
    return (error as ApiError).message;
  }
  return "Unexpected document assistance failure";
}
