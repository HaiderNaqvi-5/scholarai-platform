"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface TypedConfirmProps {
  phrase: string;
  description: string;
  buttonLabel: string;
  destructive?: boolean;
  onConfirm: () => Promise<void> | void;
}

/**
 * Typed-confirm input — requires the user to type a verbatim phrase
 * (Front-upgrade §6.23 Danger tab). Submission is blocked until exact
 * match. No checkbox shortcut.
 */
export function TypedConfirm({
  phrase,
  description,
  buttonLabel,
  destructive,
  onConfirm,
}: TypedConfirmProps) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const match = value === phrase;

  const submit = async () => {
    if (!match) return;
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  };

  const id = "typed-confirm-input";
  const helperId = "typed-confirm-helper";

  return (
    <div className="space-y-3">
      <p id={helperId} className="text-[13px] text-ink-muted">
        {description}
      </p>
      <div className="space-y-2">
        <Label htmlFor={id}>
          Type <code className="font-mono text-ink-deep">{phrase}</code> to confirm
        </Label>
        <Input
          id={id}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={phrase}
          aria-describedby={helperId}
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
        />
      </div>
      <Button
        type="button"
        variant={destructive ? "danger" : "primary"}
        size="md"
        loading={busy}
        disabled={!match}
        onClick={submit}
        aria-disabled={!match}
      >
        {buttonLabel}
      </Button>
    </div>
  );
}
