import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LegalViewer, titleFor } from "@/components/legal/LegalViewer";
import type { LegalDocument } from "@/lib/api/types";
import { API_BASE_URL } from "@/lib/api";
import "./print.css";

export const dynamic = "force-dynamic";

const SLUGS = ["terms", "privacy", "dpa", "cookie", "refund"];

export function generateStaticParams() {
  return SLUGS.map((slug) => ({ slug }));
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

async function fetchDocument(slug: string): Promise<LegalDocument | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/privacy/legal/${encodeURIComponent(slug)}`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`Failed to load /legal/${slug} (${res.status})`);
    return (await res.json()) as LegalDocument;
  } catch (err) {
    if (process.env.NODE_ENV !== "production") {
      console.error(`[legal] fetch failed for ${slug}:`, err);
    }
    return null;
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  if (!SLUGS.includes(slug)) return { title: "Not found — AidwiseAI" };
  return { title: `${titleFor(slug)} — AidwiseAI` };
}

export default async function LegalPage({ params }: PageProps) {
  const { slug } = await params;
  if (!SLUGS.includes(slug)) notFound();
  const doc = await fetchDocument(slug);
  if (!doc) {
    return (
      <main className="mx-auto flex max-w-[720px] flex-col items-center px-6 py-20 text-center">
        <h1 className="font-display text-[32px] italic font-[450] leading-[1.1] text-ink-deep">
          We couldn&rsquo;t load that document.
        </h1>
        <p className="mt-4 text-[15px] leading-[1.6] text-ink-muted">
          Try again in a moment, or view all policies at the bottom of any page.
        </p>
      </main>
    );
  }
  return <LegalViewer doc={doc} title={titleFor(slug)} />;
}
