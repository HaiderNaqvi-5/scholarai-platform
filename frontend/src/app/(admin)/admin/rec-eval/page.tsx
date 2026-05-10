import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Rec eval" };
export default function RecEvalPage() {
  return (
    <PlaceholderRoute
      title="Recommendation evaluation"
      blurb="Run benchmarks: precision@k, recall@k, nDCG@k, MRR@k. Per-case breakdown plus KPI gate pass/fail."
      sprint="Sprint 9"
    />
  );
}
