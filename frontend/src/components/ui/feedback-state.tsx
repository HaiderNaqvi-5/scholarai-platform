import type { ReactNode } from "react";

type FeedbackNoticeProps = {
  message: string;
  variant?: "error" | "success" | "info";
};

type ErrorStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
  testId?: string;
};

export function FeedbackNotice({
  message,
  variant = "info",
}: FeedbackNoticeProps) {
  const role = variant === "error" ? "alert" : "status";
  return (
    <div className={`feedback-notice feedback-notice--${variant}`} role={role}>
      <p className="body-copy">{message}</p>
    </div>
  );
}

export function ErrorState({ title, description, action, testId }: ErrorStateProps) {
  return (
    <section className="surface-card" data-testid={testId} role="alert">
      <div className="section-header">
        <p className="section-eyebrow">Error</p>
        <h2 className="section-title">{title}</h2>
        <p className="body-copy">{description}</p>
      </div>
      {action ? <div className="dashboard-actions">{action}</div> : null}
    </section>
  );
}
