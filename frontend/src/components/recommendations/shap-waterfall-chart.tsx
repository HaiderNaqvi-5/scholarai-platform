"use client";

import type { RecommendationItem } from "@/lib/types";

export function ShapWaterfallChart({
  shapExplanation,
}: {
  shapExplanation?: RecommendationItem["shap_explanation"];
}) {
  if (!shapExplanation) return null;

  const features = Object.entries(shapExplanation).sort(
    (a, b) => Math.abs(b[1]) - Math.abs(a[1]),
  );
  
  // Guard against empty dict
  if (features.length === 0) return null;

  const maxVal = Math.max(...features.map(([, v]) => Math.abs(v)), 0.01);

  return (
    <div className="shap-waterfall mt-4 pt-4 border-t border-ink-950/5">
      <p className="list-label mb-3">Profile Impact Analysis</p>
      <div className="grid gap-2">
        {features.map(([feature, value]) => {
          const percentage = (Math.abs(value) / maxVal) * 100;
          const isPositive = value >= 0;

          return (
            <div key={feature} className="flex items-center gap-3">
              <span className="text-[10px] font-bold uppercase tracking-widest w-28 truncate text-ink-700">
                {feature.replace(/_/g, " ")}
              </span>
              <div className="flex-1 bg-ink-950/5 rounded-full h-1.5 overflow-hidden flex">
                <div
                  className={`h-full rounded-full transition-all duration-700 ease-out ${
                    isPositive ? "bg-sage-600" : "bg-coral-600"
                  }`}
                  style={{
                    width: `${percentage}%`,
                  }}
                />
              </div>
              <span
                className={`text-[10px] font-mono font-bold w-10 text-right ${
                  isPositive ? "text-sage-600" : "text-coral-600"
                }`}
              >
                {isPositive ? "+" : ""}
                {value.toFixed(2)}
              </span>
            </div>
          );
        })}
      </div>
      <p className="text-[10px] mt-3 opacity-60 leading-relaxed">
        <strong>SHAP Insight:</strong> Green bars indicate features that increased your match probability. Red bars indicate profile misalignments that lowered the score.
      </p>
    </div>
  );
}
