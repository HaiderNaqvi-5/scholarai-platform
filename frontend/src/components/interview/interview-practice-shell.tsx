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
    if (!accessToken) {
      return;
    }

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
        if (!isActive) {
          return;
        }
        setState({
          isLoading: false,
          isStarting: false,
          isSubmitting: false,
          error: null,
          session,
        });
      } catch (error) {
        if (!isActive) {
          return;
        }
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
    if (!accessToken) {
      return;
    }

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
    if (!accessToken || !state.session) {
      return;
    }

    if (answerText.trim().length < 50) {
      setState((current) => ({
        ...current,
        error: "Write at least 50 characters before submitting an interview answer.",
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
      title="Practice scholarship interview answers in a text-first, rubric-based workspace."
      description="Interview practice stays focused and explainable so the feedback reads like coaching, not performance theater."
      eyebrow="Interview practice"
      intro={
        <div className="surface-band">
          <div className="button-row">
            <StatusBadge label="Rules-based scoring" variant="validated" />
            <StatusBadge label="Text-first practice" variant="generated" />
          </div>
          <p className="body-copy">
            The MVP uses one bounded session flow so the feedback remains readable and comparable.
          </p>
        </div>
      }
    >
      <section className="interview-hero" data-testid="interview-practice-shell">
        <div>
          <p className="section-eyebrow">Practice workspace</p>
          <h2 className="section-title">
            Practice one focused session at a time with direct, modest coaching.
          </h2>
          <p className="body-copy">
            The system uses a fixed rubric for clarity, relevance, confidence,
            and specificity. It does not simulate a live conversational
            interviewer in this MVP slice.
          </p>
        </div>
        <div className="interview-hero__badges">
          <StatusBadge label="Rules-based scoring" variant="validated" />
          <StatusBadge label="Text first" variant="generated" />
        </div>
      </section>

      {state.error ? (
        <section className="surface-card" data-testid="interview-error">
          <p className="section-eyebrow">Interview practice error</p>
          <h2 className="section-title">The session needs attention.</h2>
          <p className="body-copy">{state.error}</p>
        </section>
      ) : null}

      <section className="interview-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="Session entry"
            title="Start or resume a focused session"
            description="The question set stays intentionally narrow so scoring remains consistent and easy to interpret."
          />

          {state.isLoading ? (
            <p className="body-copy">Loading your latest interview session.</p>
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
                <p className="body-copy">
                  Continue this session or review the latest rubric feedback below.
                </p>
              </article>
              <div className="document-actions">
                <button
                  className="auth-link auth-link--secondary"
                  data-testid="interview-start-new-session"
                  disabled={state.isStarting}
                  onClick={() => void startSession()}
                  type="button"
                >
                  {state.isStarting ? "Starting new session" : "Start new session"}
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                No active session is stored yet. Start one fixed-text practice
                run to see question flow and rubric feedback.
              </p>
              <button
                className="auth-link auth-link--primary"
                data-testid="interview-start-session"
                disabled={state.isStarting}
                onClick={() => void startSession()}
                type="button"
              >
                {state.isStarting ? "Starting session" : "Start practice session"}
              </button>
            </div>
          )}
        </article>

        <article className="surface-panel" data-testid="interview-question-panel">
          <PageHeader
            eyebrow="Current question"
            title="Current prompt"
            description="Questions stay fixed and modest so the feedback emphasizes structure, clarity, and specificity."
          />
          {currentQuestion?.question_text ? (
            <div className="surface-list">
              <article className="question-card">
                <div className="meta-row">
                  <StatusBadge label={`Question ${currentQuestion.question_index}`} variant="planned" />
                  <span className="route-card__label">
                    {currentQuestion.total_questions} total questions
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
                    placeholder="Write a direct answer with one concrete example and a clear takeaway."
                    rows={10}
                    value={answerText}
                  />
                  <span className="field-note">
                    Minimum 50 characters. Focus on one direct answer rather than a long transcript.
                  </span>
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
                    {state.isSubmitting ? "Scoring answer" : "Submit answer"}
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                {state.session?.status === "completed"
                  ? "This session is complete. Review the results below or start a new one."
                  : "Start a session to reveal the first question."}
              </p>
            </div>
          )}
        </article>
      </section>

      <section className="interview-grid">
        <article className="surface-card" data-testid="interview-result-view">
          <PageHeader
            eyebrow="Latest result"
            title="Structured rubric feedback"
            description="Scores stay coarse and explainable so the feedback reads as guidance rather than false precision."
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
                    Average rubric score {state.session.latest_feedback.overall_score}
                  </span>
                </div>
                <p className="body-copy">{state.session.latest_feedback.summary_feedback}</p>
              </article>
              <div className="score-grid">
                {state.session.latest_feedback.dimensions.map((dimension) => (
                  <article className="score-card" key={dimension.dimension}>
                    <p className="list-label">{dimension.dimension}</p>
                    <strong>{dimension.band}</strong>
                    <p className="body-copy">Score {dimension.score} / 4</p>
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
                <p className="list-heading">Improvement prompts</p>
                <ul className="detail-list">
                  {state.session.latest_feedback.improvement_prompts.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="guidance-callout">
                <p className="list-heading">Limitation notice</p>
                <p className="body-copy">
                  {state.session.latest_feedback.limitation_notice}
                </p>
              </article>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Submit the first answer to populate the scoring and feedback panel.
              </p>
            </div>
          )}
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Session summary"
            title="Question-by-question record"
            description="The session log keeps only the minimum answer and rubric history needed for review."
          />
          {state.session?.responses.length ? (
            <div className="surface-list">
              {state.session.responses.map((response) => (
                <article key={`${response.question_index}-${response.created_at ?? "pending"}`}>
                  <div className="meta-row">
                    <StatusBadge
                      label={`Question ${response.question_index + 1}`}
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
                Session answers and scores will appear here as you progress.
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
