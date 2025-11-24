"use client";

import { useEffect, useState } from "react";

type RunRecord = {
  id: number;
  timestamp: number;
  band: string;
  provider: string;
  model: string;
  latency_ms: number;
  router_latency_ms?: number | null;
  provider_latency_ms?: number | null;
  processing_latency_ms?: number | null;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  baseline_cost_usd: number;
  savings_usd: number;
  alri_score?: number | null;
  alri_tier?: string | null;
};

type LogsResponse = {
  total: number;
  offset: number;
  limit: number;
  items: RunRecord[];
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function LogsPage() {
  const [data, setData] = useState<LogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const loadPage = async (newOffset: number) => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(
        `${API_BASE}/v1/logs?offset=${newOffset}&limit=${limit}`,
      );
      if (!res.ok) throw new Error(`API ${res.status}`);
      const json = (await res.json()) as LogsResponse;
      setData(json);
      setOffset(newOffset);
    } catch (e: any) {
      console.error(e);
      setError(e?.message ?? "Failed to load logs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPage(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const items = data?.items ?? [];
  const canPrev = offset > 0;
  const canNext = data ? offset + limit < data.total : false;

  const formatTime = (ts: number) =>
    new Date(ts * 1000).toLocaleString(undefined, {
      hour12: false,
    });

  const formatAlri = (score?: number | null, tier?: string | null) => {
    if (score == null) return "—";
    const scoreText = score % 1 === 0 ? score.toFixed(0) : score.toFixed(1);
    const tierLabel = tier ? tier.replace(/_/g, " ") : "";
    return tierLabel ? `${scoreText} (${tierLabel})` : scoreText;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <main className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Usage logs</h1>
            <p className="text-sm text-slate-400">
              Every routed call with provider, model, latency, tokens, and cost.
            </p>
          </div>
          <div className="text-xs text-slate-500">
            API base: <span className="font-mono">{API_BASE}</span>
          </div>
        </header>

        {loading && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-400">
            Loading logs…
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-red-500/40 bg-red-900/30 p-4 text-sm text-red-100">
            {error}
          </div>
        )}

        {!loading && !error && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60">
            <div className="flex flex-col gap-3 border-b border-slate-800 px-4 py-3 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
              <span>
                Showing {items.length} of {data?.total ?? 0} runs
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => loadPage(Math.max(0, offset - limit))}
                  disabled={!canPrev}
                  className="rounded-full border border-slate-700 px-3 py-1 text-xs disabled:opacity-40"
                >
                  Prev
                </button>
                <button
                  onClick={() => loadPage(offset + limit)}
                  disabled={!canNext}
                  className="rounded-full border border-slate-700 px-3 py-1 text-xs disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="bg-slate-900/80 text-slate-400">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Time</th>
                    <th className="px-4 py-2 text-left font-medium">Band</th>
                    <th className="px-4 py-2 text-left font-medium">Provider</th>
                    <th className="px-4 py-2 text-left font-medium">Model</th>
                    <th className="px-4 py-2 text-right font-medium">
                      Latency
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      Tokens
                    </th>
                    <th className="px-4 py-2 text-right font-medium">Cost</th>
                    <th className="px-4 py-2 text-right font-medium">
                      Saved vs gpt-4o
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      ALRI
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr>
                      <td
                        colSpan={9}
                        className="px-4 py-6 text-center text-slate-500"
                      >
                        No runs recorded yet.
                      </td>
                    </tr>
                  ) : (
                    items.map((r) => (
                      <tr
                        key={r.id}
                        className="border-t border-slate-800/70 text-slate-100"
                      >
                        <td className="px-4 py-2">{formatTime(r.timestamp)}</td>
                        <td className="px-4 py-2 uppercase text-slate-400">
                          {r.band}
                        </td>
                        <td className="px-4 py-2 capitalize">{r.provider}</td>
                        <td className="px-4 py-2 font-mono text-[11px]">
                          {r.model}
                        </td>
                        <td className="px-4 py-2 text-right">
                          {(r.latency_ms / 1000).toFixed(3)} s
                          {r.router_latency_ms != null &&
                            r.provider_latency_ms != null &&
                            r.processing_latency_ms != null && (
                              <div className="mt-1 text-[11px] text-slate-400">
                                Router {(r.router_latency_ms / 1000).toFixed(3)} s · Provider{" "}
                                {(r.provider_latency_ms / 1000).toFixed(3)} s · Processing{" "}
                                {(r.processing_latency_ms / 1000).toFixed(3)} s
                              </div>
                            )}
                        </td>
                        <td className="px-4 py-2 text-right">
                          {r.prompt_tokens + r.completion_tokens}
                        </td>
                        <td className="px-4 py-2 text-right">
                          ${r.cost_usd.toFixed(6)}
                        </td>
                        <td
                          className={`px-4 py-2 text-right ${
                            r.savings_usd >= 0
                              ? "text-emerald-400"
                              : "text-rose-400"
                          }`}
                        >
                          {r.savings_usd >= 0 ? "+" : ""}
                          {r.savings_usd.toFixed(6)}
                        </td>
                        <td className="px-4 py-2 text-right text-slate-200">
                          {formatAlri(r.alri_score, r.alri_tier)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
