"use client";

import { Button } from "@/components/ui/button";

interface StickySaveFooterProps {
  dirty: boolean;
  saving?: boolean;
  onSave: () => void;
  onReset?: () => void;
}

/**
 * Sticky save footer for /profile + /settings. Slides up only when the
 * form is dirty. ~Front-upgrade §6.22.
 */
export function StickySaveFooter({ dirty, saving, onSave, onReset }: StickySaveFooterProps) {
  if (!dirty) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className="sticky bottom-4 z-30 mt-6 flex items-center justify-between gap-3 rounded-[16px] border border-[var(--color-border)] bg-paper-white/95 px-4 py-3 shadow-[var(--shadow-lift)] backdrop-blur"
    >
      <span className="text-[13px] text-ink-muted">Unsaved changes.</span>
      <div className="flex items-center gap-2">
        {onReset ? (
          <Button type="button" variant="ghost" size="sm" onClick={onReset} disabled={saving}>
            Discard
          </Button>
        ) : null}
        <Button type="button" size="sm" loading={saving} onClick={onSave}>
          Save changes
        </Button>
      </div>
    </div>
  );
}
