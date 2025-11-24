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
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

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
  const sortedItems = [...items].sort((a, b) => {
    if (!sortKey) return 0;
    const dir = sortDir === "asc" ? 1 : -1;
    const getValue = (record: RunRecord) => {
      switch (sortKey) {
        case "time":
          return record.timestamp;
        case "band":
          return record.band.toLowerCase();
        case "provider":
          return record.provider.toLowerCase();
        case "model":
          return record.model.toLowerCase();
        case "latency":
          return record.latency_ms;
        case "tokens":
          return record.prompt_tokens + record.completion_tokens;
        case "cost":
          return record.cost_usd;
        case "savings":
          return record.savings_usd;
        case "alri":
          return record.alri_score ?? -Infinity;
        default:
          return 0;
      }
    };
    const valA = getValue(a);
    const valB = getValue(b);
    if (typeof valA === "string" && typeof valB === "string") {
      return valA.localeCompare(valB) * dir;
    }
    return (Number(valA) - Number(valB)) * dir;
  });

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const alriColor = (tier?: string | null) => {
    switch (tier) {
      case "red_critical":
        return "bg-rose-400";
      case "orange_high":
        return "bg-orange-400";
      case "yellow_medium":
        return "bg-amber-300";
      case "green_low":
        return "bg-emerald-400";
      default:
        return "bg-slate-500";
    }
  };

  const sortIconClass = (key: string) =>
    `ml-1 text-xs text-slate-400 transition hover:text-slate-200 ${
      sortKey === key ? "text-emerald-300" : ""
    }`;

  const SortIcon = ({ column }: { column: string }) => (
    <button
      onClick={() => handleSort(column)}
      className={sortIconClass(column)}
      aria-label={`Sort by ${column}`}
    >
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <line x1="4" y1="6" x2="20" y2="6" />
        <line x1="8" y1="12" x2="16" y2="12" />
        <line x1="10" y1="18" x2="14" y2="18" />
      </svg>
    </button>
  );

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
                Showing {sortedItems.length} of {data?.total ?? 0} runs
              </span>
              <div className="flex items-center gap-2">
                {sortKey && (
                  <span className="text-[11px] uppercase tracking-wide text-emerald-300">
                    Sorted by {sortKey} ({sortDir})
                  </span>
                )}
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
                    <th className="px-4 py-2 text-left font-medium">
                      <div className="flex items-center gap-1">
                        Time
                        <SortIcon column="time" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left font-medium">
                      <div className="flex items-center gap-1">
                        Band
                        <SortIcon column="band" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left font-medium">
                      <div className="flex items-center gap-1">
                        Provider
                        <SortIcon column="provider" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left font-medium">
                      <div className="flex items-center gap-1">
                        Model
                        <SortIcon column="model" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      <div className="flex items-center justify-end gap-1">
                        Latency
                        <SortIcon column="latency" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      <div className="flex items-center justify-end gap-1">
                        Tokens
                        <SortIcon column="tokens" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      <div className="flex items-center justify-end gap-1">
                        Cost
                        <SortIcon column="cost" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      <div className="flex items-center justify-end gap-1">
                        Saved vs gpt-4o
                        <SortIcon column="savings" />
                      </div>
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      <div className="flex items-center justify-end gap-1">
                        ALRI
                        <SortIcon column="alri" />
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedItems.length === 0 ? (
                    <tr>
                      <td
                        colSpan={9}
                        className="px-4 py-6 text-center text-slate-500"
                      >
                        No runs recorded yet.
                      </td>
                    </tr>
                  ) : (
                    sortedItems.map((r) => (
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
                          {r.alri_score != null ? (
                            <div className="inline-flex items-center justify-end gap-2">
                              <span
                                className={`h-2.5 w-2.5 rounded-full ${alriColor(
                                  r.alri_tier,
                                )}`}
                              />
                              <span>{formatAlri(r.alri_score, r.alri_tier)}</span>
                            </div>
                          ) : (
                            "-"
                          )}
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
