"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  InterviewCurrentQuestion,
  InterviewSessionSummary,
} from "@/lib/types";

const LATEST_SESSION_KEY = "scholarai.latest_interview_session";

type InterviewState = {
  isLoading: boolean;
  isStarting: boolean;
  isSubmitting: boolean;
  error: string | null;
  session: InterviewSessionSummary | null;
};

export function InterviewPracticeShell() {
  const { accessToken } = useAuth();
  const [answerText, setAnswerText] = useState("");
  const [state, setState] = useState<InterviewState>({
    isLoading: true,
    isStarting: false,
    isSubmitting: false,
    error: null,
    session: null,
  });

  useEffect(() => {
    if (!accessToken) return;

    const sessionId = localStorage.getItem(LATEST_SESSION_KEY);
    if (!sessionId) {
      setState((current) => ({ ...current, isLoading: false }));
      return;
    }

    let isActive = true;

    const loadSession = async () => {
      try {
        const session = await apiRequest<InterviewSessionSummary>(
          `/interviews/${sessionId}`,
          { token: accessToken },
        );
        if (!isActive) return;
        setState({
          isLoading: false,
          isStarting: false,
          isSubmitting: false,
          error: null,
          session,
        });
      } catch (error) {
        if (!isActive) return;
        localStorage.removeItem(LATEST_SESSION_KEY);
        setState((current) => ({
          ...current,
          isLoading: false,
          error: resolveErrorMessage(error),
          session: null,
        }));
      }
    };

    void loadSession();

    return () => {
      isActive = false;
    };
  }, [accessToken]);

  const currentQuestion = useMemo<InterviewCurrentQuestion | null>(
    () => state.session?.current_question ?? null,
    [state.session],
  );

  const startSession = async () => {
    if (!accessToken) return;

    setState((current) => ({ ...current, isStarting: true, error: null }));
    try {
      const session = await apiRequest<InterviewSessionSummary>("/interviews", {
        method: "POST",
        body: JSON.stringify({ practice_mode: "general" }),
        token: accessToken,
      });
      localStorage.setItem(LATEST_SESSION_KEY, session.session_id);
      setAnswerText("");
      setState({
        isLoading: false,
        isStarting: false,
        isSubmitting: false,
        error: null,
        session,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        isStarting: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  const submitAnswer = async () => {
    if (!accessToken || !state.session) return;

    if (answerText.trim().length < 50) {
      setState((current) => ({
        ...current,
        error: "Write at least 50 characters before submitting.",
      }));
      return;
    }

    setState((current) => ({ ...current, isSubmitting: true, error: null }));
    try {
      const session = await apiRequest<InterviewSessionSummary>(
        `/interviews/${state.session.session_id}/responses`,
        {
          method: "POST",
          body: JSON.stringify({ answer_text: answerText.trim() }),
          token: accessToken,
        },
      );
      localStorage.setItem(LATEST_SESSION_KEY, session.session_id);
      setAnswerText("");
      setState((current) => ({
        ...current,
        isSubmitting: false,
        session,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSubmitting: false,
        error: resolveErrorMessage(error),
      }));
    }
  };

  return (
    <AppShell
      title="Practice scholarship interview answers."
      description="Text-first practice with rubric-based scoring on clarity, relevance, confidence, and specificity."
      eyebrow="Interview"
      intro={
        <div className="meta-row">
          <StatusBadge label="Rubric-based scoring" variant="validated" />
          <StatusBadge label="Text practice" variant="generated" />
        </div>
      }
    >
      {state.error ? (
        <section className="surface-card" data-testid="interview-error">
          <p className="form-error">{state.error}</p>
        </section>
      ) : null}

      <section className="interview-grid" data-testid="interview-practice-shell">
        <article className="surface-card">
          <PageHeader
            eyebrow="Session"
            title="Start or resume practice"
            description="Each session has a fixed set of questions for consistent scoring."
          />

          {state.isLoading ? (
            <p className="body-copy">Loading session…</p>
          ) : state.session ? (
            <div className="surface-list">
              <article>
                <div className="meta-row">
                  <StatusBadge
                    label={
                      state.session.status === "completed"
                        ? "Completed"
                        : "In progress"
                    }
                    variant={
                      state.session.status === "completed"
                        ? "validated"
                        : "generated"
                    }
                  />
                  <span className="route-card__label">
                    {state.session.current_question_index} of {state.session.total_questions} answered
                  </span>
                </div>
              </article>
              <div className="document-actions">
                <button
                  className="auth-link auth-link--secondary"
                  data-testid="interview-start-new-session"
                  disabled={state.isStarting}
                  onClick={() => void startSession()}
                  type="button"
                >
                  {state.isStarting ? "Starting…" : "New session"}
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                No active session. Start a practice run to see questions and rubric feedback.
              </p>
              <button
                className="auth-link auth-link--primary"
                data-testid="interview-start-session"
                disabled={state.isStarting}
                onClick={() => void startSession()}
                type="button"
              >
                {state.isStarting ? "Starting…" : "Start session"}
              </button>
            </div>
          )}
        </article>

        <article className="surface-panel" data-testid="interview-question-panel">
          <PageHeader
            eyebrow="Question"
            title="Current prompt"
            description="Respond with a clear, specific answer."
          />
          {currentQuestion?.question_text ? (
            <div className="surface-list">
              <article className="question-card">
                <div className="meta-row">
                  <StatusBadge label={`Q${currentQuestion.question_index}`} variant="planned" />
                  <span className="route-card__label">
                    {currentQuestion.total_questions} total
                  </span>
                </div>
                <p className="body-copy">{currentQuestion.question_text}</p>
              </article>
              {state.session?.status !== "completed" ? (
                <label className="form-field">
                  <span className="form-field__label">Your answer</span>
                  <textarea
                    className="text-area"
                    data-testid="interview-answer-input"
                    name="interview_answer"
                    onChange={(event) => setAnswerText(event.target.value)}
                    placeholder="Write a direct answer with one concrete example."
                    rows={10}
                    value={answerText}
                  />
                  <span className="field-note">Minimum 50 characters.</span>
                </label>
              ) : null}
              {state.session?.status !== "completed" ? (
                <div className="document-actions">
                  <button
                    className="auth-link auth-link--primary"
                    data-testid="interview-submit-answer"
                    disabled={state.isSubmitting}
                    onClick={() => void submitAnswer()}
                    type="button"
                  >
                    {state.isSubmitting ? "Scoring…" : "Submit answer"}
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                {state.session?.status === "completed"
                  ? "Session complete. Review results below or start a new one."
                  : "Start a session to see the first question."}
              </p>
            </div>
          )}
        </article>
      </section>

      <section className="interview-grid">
        <article className="surface-card" data-testid="interview-result-view">
          <PageHeader
            eyebrow="Feedback"
            title="Rubric scores"
            description="Coarse scoring for clarity, relevance, confidence, and specificity."
          />
          {state.session?.latest_feedback ? (
            <div className="surface-list">
              <article>
                <div className="meta-row">
                  <StatusBadge
                    label={state.session.latest_feedback.overall_band}
                    variant="validated"
                  />
                  <span className="route-card__label">
                    Score {state.session.latest_feedback.overall_score}
                  </span>
                </div>
                <p className="body-copy">{state.session.latest_feedback.summary_feedback}</p>
              </article>
              <div className="score-grid">
                {state.session.latest_feedback.dimensions.map((dimension) => (
                  <article className="score-card" key={dimension.dimension}>
                    <p className="list-label">{dimension.dimension}</p>
                    <strong>{dimension.band}</strong>
                    <p className="body-copy">{dimension.score} / 4</p>
                  </article>
                ))}
              </div>
              <article>
                <p className="list-heading">Strengths</p>
                <ul className="detail-list">
                  {state.session.latest_feedback.strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article>
                <p className="list-heading">Improvements</p>
                <ul className="detail-list">
                  {state.session.latest_feedback.improvement_prompts.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="guidance-callout">
                <p className="list-heading">Limitation</p>
                <p className="body-copy">
                  {state.session.latest_feedback.limitation_notice}
                </p>
              </article>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Submit your first answer to see scoring and feedback.
              </p>
            </div>
          )}
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="History"
            title="Session log"
            description="Answers and scores from this session."
          />
          {state.session?.responses.length ? (
            <div className="surface-list">
              {state.session.responses.map((response) => (
                <article key={`${response.question_index}-${response.created_at ?? "pending"}`}>
                  <div className="meta-row">
                    <StatusBadge
                      label={`Q${response.question_index + 1}`}
                      variant="planned"
                    />
                    <span className="route-card__label">
                      {response.overall_band} · {response.overall_score}
                    </span>
                  </div>
                  <p className="body-copy">{response.question_text}</p>
                  <p className="code-note">{response.answer_text}</p>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Answers and scores will appear here as you progress.
              </p>
            </div>
          )}
        </article>
      </section>
    </AppShell>
  );
}

function resolveErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "message" in error) {
    return (error as ApiError).message;
  }
  return "Unexpected interview practice failure";
}
