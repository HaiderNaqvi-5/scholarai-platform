"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { SkeletonLine, SkeletonCard } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { Capability, hasCapability } from "@/lib/authorization";
import { getMentorPendingReviews, getMentorDocument, submitMentorFeedback } from "@/lib/api";
import type { 
  DocumentRecordSummary, 
  DocumentDetail, 
  MentorFeedbackRequest 
} from "@/lib/types";

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function MentorDashboardShell() {
  const { accessToken, currentUser } = useAuth();
  const canReviewDocuments = hasCapability(
    currentUser,
    accessToken,
    Capability.DocumentMentorReview,
  );
  const canSubmitFeedback = hasCapability(
    currentUser,
    accessToken,
    Capability.DocumentMentorSubmit,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingReviews, setPendingReviews] = useState<DocumentRecordSummary[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    if (!canReviewDocuments) {
      setPendingReviews([]);
      setSelectedDocument(null);
      setIsLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        setIsLoading(true);
        const data = await getMentorPendingReviews(accessToken);
        setPendingReviews(data.items);
      } catch (error: unknown) {
        setError(getErrorMessage(error, "Failed to load pending reviews."));
      } finally {
        setIsLoading(false);
      }
    };

    void loadData();
  }, [accessToken, canReviewDocuments]);

  const handleSelectDocument = async (docId: string) => {
    if (!accessToken || !canReviewDocuments) return;
    try {
      setSelectedDocument(null);
      const doc = await getMentorDocument(docId, accessToken);
      setSelectedDocument(doc);
    } catch (error: unknown) {
      setError(getErrorMessage(error, "Failed to load document content."));
    }
  };

  const handleSubmitFeedback = async (feedback: MentorFeedbackRequest) => {
    if (!accessToken || !selectedDocument) return;
    if (!canSubmitFeedback) {
      setError("You do not have permission to submit mentor feedback.");
      return;
    }
    try {
      setIsSubmitting(true);
      await submitMentorFeedback(selectedDocument.id, feedback, accessToken);
      // Refresh list and clear selection
      const data = await getMentorPendingReviews(accessToken);
      setPendingReviews(data.items);
      setSelectedDocument(null);
    } catch (error: unknown) {
      setError(getErrorMessage(error, "Failed to submit feedback."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell
      eyebrow="Mentor Workspace"
      title="Review student documents."
      description="View pending SOPs, check AI feedback, and provide human guidance."
    >
      <div className="dashboard-grid">
        <aside className="surface-panel">
          <PageHeader
            eyebrow="Queue"
            title="Pending Reviews"
            description="Documents awaiting your human feedback."
          />
          {!canReviewDocuments ? (
            <EmptyState
              title="Review access required"
              description="You do not have permission to open mentor review documents."
            />
          ) : isLoading ? (
            <div className="surface-list">
              <SkeletonLine count={3} />
            </div>
          ) : pendingReviews.length > 0 ? (
            <div className="surface-list">
              {pendingReviews.map((doc) => (
                <button
                  key={doc.id}
                  className={`list-item-btn ${selectedDocument?.id === doc.id ? "active" : ""}`}
                  disabled={!canReviewDocuments}
                  onClick={() => void handleSelectDocument(doc.id)}
                >
                  <div className="meta-row">
                    <StatusBadge label={doc.document_type} variant="generated" />
                    <span className="route-card__label">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h4 className="list-item-title">{doc.title || "Untitled Document"}</h4>
                  <p className="list-item-sub">By Candidate ID: {doc.id.split("-")[0]}</p>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState
              title="All caught up"
              description="There are no pending documents in the queue."
            />
          )}
        </aside>

        <main className="surface-card">
          {selectedDocument ? (
            <MentorReviewWorkspace
              document={selectedDocument}
              onSubmit={handleSubmitFeedback}
              isSubmitting={isSubmitting}
              canSubmitFeedback={canSubmitFeedback}
            />
          ) : (
            <div className="empty-panel h-full flex items-center justify-center">
              <p className="body-copy">Select a document from the queue to start reviewing.</p>
            </div>
          )}
        </main>
      </div>

      {error && (
        <section className="surface-card mt-6 border-red-200 bg-red-50">
          <p className="text-red-700 font-medium">{error}</p>
        </section>
      )}
    </AppShell>
  );
}

function MentorReviewWorkspace({
  document,
  onSubmit,
  isSubmitting,
  canSubmitFeedback,
}: {
  document: DocumentDetail;
  onSubmit: (feedback: MentorFeedbackRequest) => void;
  isSubmitting: boolean;
  canSubmitFeedback: boolean;
}) {
  const [formData, setFormData] = useState<MentorFeedbackRequest>({
    summary: "",
    strengths: [""],
    revision_priorities: [""],
    caution_notes: [""],
  });

  const handleAddField = (field: keyof MentorFeedbackRequest) => {
    if (field === "summary") return;
    setFormData((prev) => ({
      ...prev,
      [field]: [...(prev[field] as string[]), ""],
    }));
  };

  const handleFieldChange = (
    field: keyof MentorFeedbackRequest,
    index: number,
    value: string
  ) => {
    if (field === "summary") {
      setFormData((prev) => ({ ...prev, summary: value }));
      return;
    }
    const newList = [...(formData[field] as string[])];
    newList[index] = value;
    setFormData((prev) => ({ ...prev, [field]: newList }));
  };

  return (
    <div className="review-workspace">
      <div className="review-workspace__header">
        <PageHeader
          eyebrow={document.document_type.toUpperCase()}
          title={document.title || "Untitled Document"}
          description={`Created ${new Date(document.created_at).toLocaleString()}`}
        />
      </div>

      <div className="review-workspace__content grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="document-view overflow-y-auto max-h-[600px] p-6 surface-panel font-serif leading-relaxed">
          <p className="whitespace-pre-wrap">{document.content_text}</p>
        </div>

        <div className="feedback-form p-6 surface-panel overflow-y-auto max-h-[600px]">
          <h3 className="sub-heading mb-4">Provide Feedback</h3>
          <div className="form-group mb-6">
            <label className="list-heading">Summary Analysis</label>
            <textarea
              className="text-input w-full mt-2 h-32"
              placeholder="Provide a high-level critique of the document..."
              value={formData.summary}
              onChange={(e) => handleFieldChange("summary", 0, e.target.value)}
            />
          </div>

          {(["strengths", "revision_priorities", "caution_notes"] as const).map((field) => (
            <div key={field} className="form-group mb-6">
              <div className="flex justify-between items-center mb-2">
                <label className="list-heading capitalize">{field.replace("_", " ")}</label>
                <button
                  type="button"
                  className="nav-link text-xs"
                  disabled={!canSubmitFeedback}
                  onClick={() => handleAddField(field)}
                >
                  + Add Point
                </button>
              </div>
              {formData[field].map((val, idx) => (
                <input
                  key={`${field}-${idx}`}
                  type="text"
                  className="text-input w-full mb-2"
                  value={val}
                  onChange={(e) => handleFieldChange(field, idx, e.target.value)}
                  placeholder={`Enter ${field.replace("_", " ")} item...`}
                />
              ))}
            </div>
          ))}

          <button
            className="auth-link auth-link--primary w-full"
            disabled={isSubmitting || !formData.summary || !canSubmitFeedback}
            onClick={() => onSubmit(formData)}
          >
            {isSubmitting ? "Submitting..." : "Publish Feedback"}
          </button>
        </div>
      </div>

      {document.latest_feedback && (
        <div className="ai-feedback-reference mt-8 p-6 surface-panel border-l-4 border-accent">
          <h4 className="list-heading mb-2">Reference: Latest AI Feedback</h4>
          <p className="body-copy italic mb-2">{document.latest_feedback.summary}</p>
          <div className="grid grid-cols-3 gap-4 text-xs opacity-75">
            <div>
              <strong>Strengths:</strong> {document.latest_feedback.strengths.length}
            </div>
            <div>
              <strong>Revisions:</strong> {document.latest_feedback.revision_priorities.length}
            </div>
            <div>
              <strong>Citations:</strong> {document.latest_feedback.citations.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
