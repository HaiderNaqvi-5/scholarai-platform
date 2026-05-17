import { renderMarkdownBlocks } from "./markdown";
import type { LegalDocument } from "@/lib/api/types";

interface LegalViewerProps {
  doc: LegalDocument;
  title: string;
}

const SLUG_TITLES: Record<string, string> = {
  terms: "Terms of Service",
  privacy: "Privacy Notice",
  dpa: "Data Processing Addendum",
  cookie: "Cookie Policy",
  refund: "Refund Policy",
};

export function titleFor(slug: string): string {
  return SLUG_TITLES[slug] || slug;
}

function formatEffective(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

/**
 * LegalViewer — Front-upgrade §6.4.
 *
 * Fraunces 32 italic title, mono version chip, ToC sidebar (lg+),
 * body max-w 720 with 17/1.7 paragraphs. Renders backend `body_markdown`
 * using a minimal markdown subset (h2/h3/lists/paragraphs) so we don't
 * pull in a heavyweight runtime dependency.
 */
export function LegalViewer({ doc, title }: LegalViewerProps) {
  const blocks = renderMarkdownBlocks(doc.body_markdown);
  const headings = blocks
    .filter((b) => b.kind === "h2")
    .map((b) => ({ id: b.id, text: b.text }));

  return (
    <main
      data-testid="legal-doc"
      className="mx-auto flex max-w-[1200px] flex-col gap-10 px-6 py-10 md:flex-row md:gap-12 md:px-12 md:py-14"
    >
      <div className="md:flex-1 md:max-w-[720px]">
        <header className="border-b border-[var(--color-border-quiet)] pb-6">
          <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            AidwiseAI
          </p>
          <h1 className="mt-2 font-display text-[32px] italic font-[450] leading-[1.1] tracking-[-0.02em] text-ink-deep">
            {title}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-ink-muted">
            <span
              className="inline-flex h-6 items-center rounded-full bg-[var(--color-paper-warm)] px-2.5 font-mono text-[11px] text-ink-deep"
              aria-label={`Version ${doc.version}`}
            >
              v{doc.version}
            </span>
            <span>Effective {formatEffective(doc.effective_at)}</span>
            <span className="font-mono text-[11px] text-ink-subtle" title="Document hash">
              sha256 · {doc.sha256_hash.slice(0, 10)}…
            </span>
          </div>
        </header>

        <article className="mt-8 space-y-5 text-[17px] leading-[1.7] text-ink">
          {blocks.map((b) => renderBlock(b))}
        </article>
      </div>

      {headings.length > 0 ? (
        <nav
          aria-label="Section table of contents"
          className="hidden shrink-0 md:block md:w-[220px]"
        >
          <div className="sticky top-24">
            <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
              On this page
            </p>
            <ul className="mt-3 space-y-2 text-[13px]">
              {headings.map((h) => (
                <li key={h.id}>
                  <a
                    href={`#${h.id}`}
                    className="text-ink-muted underline-offset-2 hover:text-ink-deep hover:underline"
                  >
                    {h.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      ) : null}
    </main>
  );
}

import type { MarkdownBlock } from "./markdown";

function renderBlock(b: MarkdownBlock) {
  switch (b.kind) {
    case "h2":
      return (
        <h2
          key={b.id}
          id={b.id}
          className="mt-10 text-[24px] leading-[1.3] tracking-[-0.01em] text-ink-deep font-medium"
        >
          {b.text}
        </h2>
      );
    case "h3":
      return (
        <h3 key={b.id} id={b.id} className="mt-6 text-[18px] font-semibold text-ink-deep">
          {b.text}
        </h3>
      );
    case "list":
      return (
        <ul key={b.id} className="ml-5 list-disc space-y-2 text-ink">
          {b.items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      );
    case "p":
      return (
        <p key={b.id} className="text-ink">
          {b.text}
        </p>
      );
    default:
      return null;
  }
}
