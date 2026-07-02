"use client";

import { RankedCandidate } from "@/lib/types";
import ScoreBar from "./ScoreBar";

export default function CandidateCard({ candidate, rank }: { candidate: RankedCandidate; rank: number }) {
  const s = candidate.score_breakdown;

  return (
    <div className="border border-border bg-panel rounded-lg p-5 hover:border-signal/40 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-start gap-3">
          <div className="font-numeric text-muted text-sm pt-1">#{String(rank).padStart(2, "0")}</div>
          <div>
            <h3 className="text-ink font-semibold text-base leading-tight">{candidate.name}</h3>
            <p className="text-muted text-sm">{candidate.headline}</p>
            <p className="text-muted text-xs mt-0.5">{candidate.location}</p>
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="font-numeric text-2xl text-signal">{(s.final_score * 100).toFixed(0)}</div>
          <div className="text-[10px] tracking-wide text-muted">FIT SCORE</div>
        </div>
      </div>

      <p className="text-sm text-ink/90 leading-relaxed mb-4 border-l-2 border-signal/40 pl-3">
        {candidate.justification}
      </p>

      <div className="grid grid-cols-2 gap-x-6 gap-y-3 mb-4">
        <ScoreBar label="Semantic fit" value={s.semantic_score} color="#39D6C0" />
        <ScoreBar label="Implicit skills" value={s.implicit_skill_score} color="#39D6C0" />
        <ScoreBar label="Career velocity" value={s.velocity_score} color="#F2A65A" />
        <ScoreBar label="Job-hop penalty" value={s.hop_penalty} color="#F2545B" isPenalty />
      </div>

      <div className="flex flex-wrap gap-1.5 mb-2">
        {s.matched_explicit_skills.map((skill) => (
          <span key={skill} className="text-[11px] px-2 py-0.5 rounded-full bg-signal/10 text-signal border border-signal/20">
            {skill}
          </span>
        ))}
        {s.matched_implicit_skills.map((skill) => (
          <span key={skill} className="text-[11px] px-2 py-0.5 rounded-full bg-velocity/10 text-velocity border border-velocity/20">
            {skill} (inferred)
          </span>
        ))}
      </div>

      <div className="flex justify-between text-[11px] text-muted pt-2 border-t border-border mt-3">
        <span>{candidate.total_years_experience} yrs experience</span>
        <span>{candidate.promotions} promotion(s)</span>
        <span>{candidate.avg_tenure_years} yrs avg. tenure</span>
      </div>
    </div>
  );
}
