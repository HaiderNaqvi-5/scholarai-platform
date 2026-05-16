/**
 * Tracker Kanban column order + display metadata. Single source so the
 * sidebar, page, future strategy-report UI, and the demo seed stay in sync.
 * The literal union mirrors the backend `TrackerStage` enum.
 */

export type TrackerStage =
  | "researching"
  | "preparing"
  | "applied"
  | "interview"
  | "decision"
  | "accepted";

export type StageTone = "neutral" | "validated" | "caution";

export type StageMeta = {
  stage: TrackerStage;
  label: string;
  tone: StageTone;
};

export const STAGE_META: readonly StageMeta[] = [
  { stage: "researching", label: "Researching", tone: "neutral" },
  { stage: "preparing", label: "Preparing docs", tone: "neutral" },
  { stage: "applied", label: "Applied", tone: "validated" },
  { stage: "interview", label: "Interview", tone: "validated" },
  { stage: "decision", label: "Decision", tone: "caution" },
  { stage: "accepted", label: "Accepted", tone: "validated" },
] as const;

export const TRACKER_STAGES: readonly TrackerStage[] = STAGE_META.map((m) => m.stage);

export function stageLabel(stage: TrackerStage): string {
  return STAGE_META.find((m) => m.stage === stage)?.label ?? stage;
}
