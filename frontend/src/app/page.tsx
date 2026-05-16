import Link from "next/link";
import { ArrowRight, Banknote, Calendar, GraduationCap, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Landing() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <Link href="/" className="font-display text-xl tracking-tight text-ink">
          AidwiseAI
        </Link>
        <nav className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link href="/upgrade">Pricing</Link>
          </Button>
          <Button asChild variant="ghost" size="sm">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/signup">Create account</Link>
          </Button>
        </nav>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pb-16 pt-12 md:pt-24">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-ink-subtle">
          For Pakistani MS / PhD applicants
        </p>
        <h1 className="mt-3 max-w-4xl font-display text-[44px] font-semibold leading-[1.05] tracking-tight text-ink md:text-[64px]">
          Find fully-funded programs abroad.
          <span className="text-ink-muted"> No consultant. No fees.</span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-ink-muted">
          AidwiseAI helps Pakistani students discover scholarships, write
          winning SOPs, and ace visa interviews — built for HEC degrees, UK / US /
          Canada / Germany visas, and PKR-anchored honest pricing.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/signup">
              Find my scholarships <ArrowRight className="size-4" strokeWidth={2} />
            </Link>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/login">I have an account</Link>
          </Button>
        </div>
        <p className="mt-4 text-sm text-ink-subtle">
          Helping students from Karachi, Lahore, Islamabad, and beyond.
        </p>
      </section>

      {/* Problem */}
      <section className="border-t border-[var(--color-border)] bg-paper-warm/40">
        <div className="mx-auto grid max-w-6xl gap-6 px-6 py-16 md:grid-cols-2">
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
              The Pakistani applicant tax
            </p>
            <h2 className="mt-2 font-display text-3xl text-ink md:text-4xl">
              Every wrong decision is expensive.
            </h2>
            <p className="mt-4 text-ink-muted">
              Consultants charge PKR 40,000–150,000 for generic advice. WhatsApp
              groups and YouTube are noisy. Visa officers look for specific
              answers Pakistani students rarely rehearse. We built one platform
              that fixes all three.
            </p>
          </div>
          <ul className="grid gap-3 self-center">
            <Problem
              icon={<Banknote className="size-5" />}
              title="Consultants cost PKR 40,000–150,000+"
              detail="And most give the same templated SOP and university list to every student."
            />
            <Problem
              icon={<Calendar className="size-5" />}
              title="Deadlines slip in DM threads"
              detail="Chevening and DAAD have a single window per year. Miss it and you wait twelve months."
            />
            <Problem
              icon={<Mic className="size-5" />}
              title="Visa rejection rates are real"
              detail="Pakistan has some of the world's lowest approval rates — yet most students walk in without one practice round."
            />
          </ul>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
          How AidwiseAI works
        </p>
        <h2 className="mt-2 font-display text-3xl text-ink md:text-4xl">
          Four steps. One result.
        </h2>
        <div className="mt-10 grid gap-6 md:grid-cols-4">
          <Step
            n="1"
            title="Build your profile"
            body="CGPA, IELTS, target country, field. The matcher converts Pakistani CGPA to US-equivalent and UK class."
          />
          <Step
            n="2"
            title="Get matched"
            body="Scholarships and universities ranked by eligibility — Chevening, Fulbright, DAAD, HEC Overseas, Commonwealth and more."
          />
          <Step
            n="3"
            title="Write your SOP"
            body="Six-paragraph drafts tuned to Pakistani context — ties to Pakistan, return-intent narrative, HEC framing."
          />
          <Step
            n="4"
            title="Practise your visa"
            body="UK / US / Canada / Germany interview simulator with red-flag detection and sample-answer playback."
          />
        </div>
      </section>

      {/* Featured scholarships */}
      <section className="border-t border-[var(--color-border)] bg-paper-warm/40">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
            Featured scholarships
          </p>
          <h2 className="mt-2 font-display text-3xl text-ink md:text-4xl">
            Real, fully-funded, Pakistani-eligible.
          </h2>
          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <FeaturedScholarship name="Chevening" country="UK" funding="Full · ~£18,000/yr + extras" />
            <FeaturedScholarship name="Fulbright" country="USA" funding="Full · ~$35,000/yr" />
            <FeaturedScholarship name="DAAD" country="Germany" funding="Full · €934/mo + travel" />
            <FeaturedScholarship name="Commonwealth" country="UK" funding="Full · tuition + living" />
            <FeaturedScholarship name="HEC Overseas" country="Multi" funding="Full · PhD-focused" />
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid gap-4 md:grid-cols-3">
          <StatCard headline="150,000+" caption="Pakistani students currently studying abroad" />
          <StatCard headline="62%" caption="of Pakistani youth want to study abroad" />
          <StatCard headline="0" caption="dedicated AI platforms for Pakistani students — until now" />
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[var(--color-border)] bg-paper-white">
        <div className="mx-auto max-w-3xl px-6 py-16 text-center">
          <GraduationCap className="mx-auto size-8 text-ink" aria-hidden />
          <h2 className="mt-3 font-display text-3xl text-ink md:text-4xl">
            Start for free. No consultant. No fees.
          </h2>
          <p className="mt-3 text-ink-muted">
            One profile. Every scholarship you actually qualify for. Pro and
            Elite unlock unlimited drafts and full visa practice when you&apos;re
            ready.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/signup">
                Create your profile <ArrowRight className="size-4" />
              </Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link href="/upgrade">See pricing</Link>
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t border-[var(--color-border)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-ink-subtle md:flex-row md:items-center md:justify-between">
          <p>AidwiseAI · Built for Pakistani applicants.</p>
          <p className="font-mono text-xs">
            Are you a university or school?{" "}
            <Link href="/universities" className="underline">
              Partner with us →
            </Link>
          </p>
        </div>
      </footer>
    </div>
  );
}

function Problem({
  icon,
  title,
  detail,
}: {
  icon: React.ReactNode;
  title: string;
  detail: string;
}) {
  return (
    <li className="flex gap-3 rounded-[16px] border border-[var(--color-border)] bg-paper-white p-4">
      <span className="mt-0.5 text-ink" aria-hidden>
        {icon}
      </span>
      <div>
        <p className="font-medium text-ink">{title}</p>
        <p className="mt-1 text-sm text-ink-muted">{detail}</p>
      </div>
    </li>
  );
}

function Step({ n, title, body }: { n: string; title: string; body: string }) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-6">
      <p className="font-mono text-xs uppercase tracking-wider text-ink-muted">
        Step {n}
      </p>
      <h3 className="mt-2 font-display text-lg text-ink">{title}</h3>
      <p className="mt-2 text-[15px] text-ink-muted">{body}</p>
    </div>
  );
}

function FeaturedScholarship({
  name,
  country,
  funding,
}: {
  name: string;
  country: string;
  funding: string;
}) {
  return (
    <div className="rounded-[16px] border border-[var(--color-border)] bg-paper-white p-4">
      <p className="font-display text-lg text-ink">{name}</p>
      <p className="mt-1 font-mono text-xs uppercase tracking-wide text-ink-muted">
        {country}
      </p>
      <p className="mt-2 text-sm text-ink-muted">{funding}</p>
    </div>
  );
}

function StatCard({ headline, caption }: { headline: string; caption: string }) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-6 text-center">
      <p className="font-display text-4xl text-ink">{headline}</p>
      <p className="mt-2 text-sm text-ink-muted">{caption}</p>
    </div>
  );
}
