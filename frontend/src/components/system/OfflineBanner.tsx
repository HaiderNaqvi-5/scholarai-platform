"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { usePathname } from "next/navigation";

/**
 * OfflineBanner — sticky top banner that surfaces network state per
 * Front-upgrade §6.34. Hidden on /offline (the standalone page already
 * communicates the state). Mounted once globally in providers.tsx.
 *
 * Anti-slop: no emoji, no retry counter, no fake "Reconnecting…" timer.
 * The browser's `online` event is the truth.
 */

function subscribe(cb: () => void) {
  window.addEventListener("online", cb);
  window.addEventListener("offline", cb);
  return () => {
    window.removeEventListener("online", cb);
    window.removeEventListener("offline", cb);
  };
}
const getSnapshot = () => navigator.onLine;
const getServerSnapshot = () => true;

export function OfflineBanner() {
  const pathname = usePathname();
  const online = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const [justReconnected, setJustReconnected] = useState(false);
  const wasOfflineRef = useRef(false);

  useEffect(() => {
    const handleOffline = () => {
      wasOfflineRef.current = true;
    };
    const handleOnline = () => {
      if (!wasOfflineRef.current) return;
      wasOfflineRef.current = false;
      setJustReconnected(true);
      const id = window.setTimeout(() => setJustReconnected(false), 4000);
      // Cleanup via dedicated effect would be heavier than this; the
      // banner unmounts on /offline anyway, dropping the timer.
      return () => window.clearTimeout(id);
    };
    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, []);

  if (pathname === "/offline") return null;
  if (online && !justReconnected) return null;

  if (!online) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="fixed left-0 right-0 top-0 z-50 flex items-center justify-center bg-[var(--color-caution-soft)] px-4 py-2 text-[13px] text-ink-deep shadow-[var(--shadow-hairline)]"
      >
        <span>You&rsquo;re offline. Changes will sync when you reconnect.</span>
      </div>
    );
  }
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed left-0 right-0 top-0 z-50 flex items-center justify-center bg-[var(--color-validated-soft)] px-4 py-2 text-[13px] text-ink-deep shadow-[var(--shadow-hairline)]"
    >
      <span>Back online.</span>
    </div>
  );
}
