"use client";

import { useState } from "react";
import { searchCandidates } from "@/lib/api";
import { SearchResponse } from "@/lib/types";
import FunnelStrip from "@/components/FunnelStrip";
import CandidateCard from "@/components/CandidateCard";

const SAMPLE_JD =
  "Senior Backend Engineer with strong Python, FastAPI, PostgreSQL and Docker experience. " +
  "Kubernetes and AWS a plus. Looking for someone with a track record of promotions and technical leadership.";

export default function Home() {
  const [jdText, setJdText] = useState(SAMPLE_JD);
  const [blindMode, setBlindMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  async function handleSearch() {
    if (jdText.trim().length < 10) {
      setError("Enter a fuller job description (at least 10 characters).");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await searchCandidates({
        jd_text: jdText,
        top_k_semantic: 100,
        top_n_final: 5,
        blind_mode: blindMode,
      });
      setResponse(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-10">
      <header className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <span className="h-2 w-2 rounded-full bg-signal" />
          <span className="text-[11px] tracking-[0.2em] text-muted">INTELLIGENT CANDIDATE DISCOVERY</span>
        </div>
        <h1 className="text-3xl font-semibold text-ink">Find the fit, not just the keywords.</h1>
        <p className="text-muted mt-1 text-sm">
          Semantic search re-ranked by career trajectory — explainable, in under 2.5 seconds.
        </p>
      </header>

      <section className="mb-6">
        <textarea
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          rows={4}
          placeholder="Paste a job description..."
          className="w-full bg-panel border border-border rounded-lg p-4 text-sm text-ink placeholder:text-muted focus:border-signal outline-none resize-y"
        />

        <div className="flex items-center justify-between mt-3">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <button
              type="button"
              role="switch"
              aria-checked={blindMode}
              onClick={() => setBlindMode((v) => !v)}
              className={`relative w-10 h-5 rounded-full transition-colors ${
                blindMode ? "bg-signal" : "bg-panel2"
              }`}
            >
              <span
                className={`absolute top-0.5 h-4 w-4 rounded-full bg-base transition-transform ${
                  blindMode ? "translate-x-5" : "translate-x-0.5"
                }`}
              />
            </button>
            <span className="text-sm text-ink">Blind Audition Mode</span>
            <span className="text-xs text-muted">(mask PII)</span>
          </label>

          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-signal text-base font-medium text-sm px-5 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {loading ? "Scanning candidates…" : "Find candidates"}
          </button>
        </div>

        {error && <p className="text-penalty text-sm mt-2">{error}</p>}
      </section>

      <section className="mb-8">
        <FunnelStrip
          tier1={response?.candidates_considered_tier1 ?? 0}
          tier2={response?.candidates_reranked_tier2 ?? 0}
          tier3={response?.results.length ?? 0}
          latency={response?.latency_ms ?? null}
          scanning={loading}
        />
      </section>

      {response && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm tracking-widest text-muted">TOP {response.results.length} CANDIDATES</h2>
            <span className="text-[11px] font-numeric text-muted">
              total latency: {response.latency_ms.total_ms}ms
            </span>
          </div>
          <div className="grid gap-4">
            {response.results.map((c, i) => (
              <CandidateCard key={c.id} candidate={c} rank={i + 1} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
