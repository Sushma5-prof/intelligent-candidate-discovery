"use client";

interface FunnelStripProps {
  tier1: number;
  tier2: number;
  tier3: number;
  latency: Record<string, number> | null;
  scanning: boolean;
}

const STAGES = [
  { key: "tier1_net_ms", label: "THE NET", sub: "vector search · HNSW" },
  { key: "tier2_reranker_ms", label: "THE FILTER", sub: "cross-encoder rerank" },
  { key: "tier3_polish_ms", label: "THE POLISH", sub: "explainability LLM" },
];

export default function FunnelStrip({ tier1, tier2, tier3, latency, scanning }: FunnelStripProps) {
  const counts = [tier1, tier2, tier3];

  return (
    <div className="border border-border bg-panel rounded-lg overflow-hidden">
      <div className="grid grid-cols-3 divide-x divide-border">
        {STAGES.map((stage, i) => {
          const width = tier1 > 0 ? Math.max(6, (counts[i] / tier1) * 100) : 0;
          const ms = latency?.[stage.key];
          return (
            <div key={stage.key} className="relative p-4">
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-[11px] tracking-widest text-muted">{stage.label}</span>
                {scanning && (
                  <span className="relative flex h-2 w-2">
                    <span className="animate-pulse_ring absolute inline-flex h-full w-full rounded-full bg-signal" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-signal" />
                  </span>
                )}
              </div>
              <div className="font-numeric text-2xl text-ink">
                {counts[i] > 0 ? counts[i] : "—"}
              </div>
              <div className="text-[11px] text-muted mb-3">{stage.sub}</div>
              <div className="h-1 w-full bg-panel2 rounded-full overflow-hidden">
                <div
                  className="h-full bg-signal score-bar-fill rounded-full"
                  style={{ width: `${counts[i] > 0 ? width : 0}%` }}
                />
              </div>
              {ms !== undefined && (
                <div className="mt-1 text-[11px] font-numeric text-signal/80">{ms}ms</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
