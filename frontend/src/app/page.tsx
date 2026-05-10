import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Landing() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <Link href="/" className="font-display text-xl tracking-tight text-ink">
          GrantPath
        </Link>
        <nav className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/signup">Create account</Link>
          </Button>
        </nav>
      </header>

      <section className="mx-auto max-w-6xl px-6 pb-20 pt-12 md:pt-24">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-ink-subtle">
          For grad school applicants
        </p>
        <h1 className="mt-3 max-w-3xl font-display text-[44px] font-semibold leading-[1.05] tracking-tight text-ink md:text-[64px]">
          Scholarships you actually qualify for.
          <span className="text-ink-muted"> Deadlines that don&apos;t slip.</span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-ink-muted">
          GrantPath ranks scholarships against your real profile — citizenship, GPA,
          field, degree level. No probability scores. No filler. Just what fits, what
          doesn&apos;t, and the date by which to apply.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/signup">
              Get matched <ArrowRight className="size-4" strokeWidth={2} />
            </Link>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/login">I have an account</Link>
          </Button>
        </div>

        <div className="mt-20 grid gap-6 md:grid-cols-3">
          <Pillar
            title="Match by eligibility, not vibes"
            body="Citizenship, language, GPA, field, and degree level checked against published rules — never inferred."
          />
          <Pillar
            title="One tracker, no spreadsheets"
            body="Save scholarships, move them through saved → in progress → applied. Deadlines counted in days, not paragraphs."
          />
          <Pillar
            title="Drafts that survive a refresh"
            body="Statement of purpose autosaves locally every 5 seconds. Practice the interview. Show up ready."
          />
        </div>
      </section>

      <footer className="border-t border-[var(--color-border)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-ink-subtle md:flex-row md:items-center md:justify-between">
          <p>GrantPath · Built for grad school applicants.</p>
          <p className="font-mono text-xs">v0.1 SLC · Canada-first</p>
        </div>
      </footer>
    </div>
  );
}

function Pillar({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-6">
      <h3 className="font-display text-lg text-ink">{title}</h3>
      <p className="mt-2 text-[15px] text-ink-muted">{body}</p>
    </div>
  );
}
