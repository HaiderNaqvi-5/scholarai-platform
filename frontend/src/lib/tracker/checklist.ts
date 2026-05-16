/**
 * Single source of truth for the 14 tracker checklist keys + labels.
 *
 * The key set is mirrored on the backend in `app/schemas/tracker.py`
 * (`_DEFAULT_CHECKLIST_KEYS`). The frontend `TrackerChecklistKey` literal
 * union in `lib/api/types.ts` is derived from this map's keys so a new doc
 * (e.g. visa interview slot) can be added in exactly one place here.
 */

export const CHECKLIST_LABELS = {
  transcripts: "Transcripts",
  degree_certificate: "Degree certificate",
  ielts_certificate: "IELTS certificate",
  gre_scores: "GRE scores",
  sop_draft: "SOP draft",
  sop_final: "SOP final",
  cv_resume: "CV / résumé",
  lor_1: "LOR #1",
  lor_2: "LOR #2",
  lor_3: "LOR #3",
  bank_statement: "Bank statement",
  hec_attestation: "HEC Degree Attestation (required for UK/Germany)",
  passport_copy: "Passport copy",
  application_fee_paid: "Application fee paid",
} as const;

export type TrackerChecklistKey = keyof typeof CHECKLIST_LABELS;

export const CHECKLIST_KEYS = Object.keys(CHECKLIST_LABELS) as TrackerChecklistKey[];

export type TrackerChecklist = Record<TrackerChecklistKey, boolean>;

export function checklistProgress(
  checklist: TrackerChecklist | undefined,
): { done: number; total: number } {
  const total = CHECKLIST_KEYS.length;
  if (!checklist) return { done: 0, total };
  let done = 0;
  for (const key of CHECKLIST_KEYS) {
    if (checklist[key]) done += 1;
  }
  return { done, total };
}
