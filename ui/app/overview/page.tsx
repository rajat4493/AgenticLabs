"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProviderBadge } from "@/components/ProviderBadge";
import { MetricCard } from "@/components/MetricCard";

type ProviderStat = {
  provider: string;
  runs: number;
  total_cost_usd: number;
  avg_latency_ms: number;
};

type MetricsSummary = {
  total_runs: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  cost_per_run_usd: number;
  baseline_cost_usd: number | null;
  savings_vs_baseline_usd: number | null;
  savings_pct: number | null;
  what_if_cost_usd: number | null;
  what_if_vs_actual_usd: number | null;
  provider_breakdown: ProviderStat[];
  timeseries: { date: string; requests: number; cost_usd: number }[];
  avg_alri_score: number | null;
  high_alri_run_pct: number | null;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function OverviewPage() {
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_BASE}/v1/metrics/summary`);
        if (!res.ok) {
          const text = await res.text();
          throw new Error(
            `Status ${res.status} ${res.statusText}: ${text || "<no body>"}`
          );
        }

        const data = (await res.json()) as MetricsSummary;
        setSummary(data);
      } catch (err: any) {
        console.error("Failed to load metrics:", err);
        setError(err?.message ?? "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, []);

  const totalRuns = summary?.total_runs ?? 0;
  const avgLatency = summary?.avg_latency_ms ?? 0;
  const totalCost = summary?.total_cost_usd ?? 0;
  const costPerRun =
    summary?.cost_per_run_usd ??
    (totalRuns > 0 ? totalCost / Math.max(1, totalRuns) : 0);
  const baselineCost = summary?.baseline_cost_usd ?? null;
  const savingsUsd = summary?.savings_vs_baseline_usd ?? null;
  const savingsPct = summary?.savings_pct ?? null;
  const whatIfCost = summary?.what_if_cost_usd ?? null;
  const whatIfDelta = summary?.what_if_vs_actual_usd ?? null;
  const savingsDisplay =
    savingsUsd != null && savingsPct != null
      ? `$${savingsUsd.toFixed(6)} (${savingsPct.toFixed(1)}%)`
      : "—";
  const avgAlriScore = summary?.avg_alri_score ?? null;
  const highAlriRunPct = summary?.high_alri_run_pct ?? null;
  const highAlriDisplay =
    highAlriRunPct != null ? `${highAlriRunPct.toFixed(1)}%` : "—";

  return (
    <div className="min-h-screen bg-[#030712] text-slate-50">
      {/* subtle gradient wash */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,_rgba(45,212,191,0.22),_transparent_55%),radial-gradient(circle_at_bottom,_rgba(56,189,248,0.16),_transparent_55%),linear-gradient(130deg,_rgba(12,18,40,0.9)_0%,_rgba(2,8,23,0.95)_60%)]" />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-9 px-4 pb-16 pt-10 sm:px-6 lg:px-10 xl:max-w-[72rem]">
        <h1 className="text-2xl font-semibold text-white">Overview</h1>
        {/* Hero */}
        <section className="space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/40 bg-black/30 px-3 py-1 text-[11px] font-medium text-emerald-200 shadow-[0_4px_18px_rgba(16,185,129,0.35)] backdrop-blur">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            AgenticLabs · Smart Router
            <span className="hidden text-emerald-300/80 sm:inline">
              · v0.2.0-alpha Cost Dashboard
            </span>
          </div>

          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div className="space-y-3">
              <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
                <span className="bg-gradient-to-r from-emerald-300 via-cyan-200 to-sky-300 bg-clip-text text-transparent">
                  Router Overview
                </span>
              </h1>
              <p className="max-w-xl text-sm leading-relaxed text-slate-200/80">
                A live snapshot of how your traffic flows through AgenticLabs:
                how often it runs, how fast it responds, and what it&apos;s
                costing you. Designed as the starting point for your cost &
                governance story.
              </p>
              {savingsUsd != null && savingsPct != null && baselineCost != null && (
                <p className="text-sm text-emerald-200/80">
                  You saved{" "}
                  <span className="font-semibold text-emerald-100">
                    ${savingsUsd.toFixed(6)}
                  </span>{" "}
                  ({savingsPct.toFixed(1)}%) vs a baseline of{" "}
                  <span className="font-semibold text-emerald-100">
                    ${baselineCost.toFixed(6)}
                  </span>
                  .
                </p>
              )}
            </div>

            <div className="space-y-1 text-right text-[11px] text-slate-400">
              <p>
                API base:&nbsp;
                <span className="font-mono text-slate-200">{API_BASE}</span>
              </p>
              <p>Summary: /v1/metrics/summary</p>
            </div>
          </div>
        </section>

        {/* States */}
        {loading && (
          <div className="rounded-2xl border border-slate-800/70 bg-black/30 px-4 py-3 text-sm text-slate-200 shadow-[0_12px_24px_rgba(2,6,23,0.6)] backdrop-blur">
            Loading metrics…
          </div>
        )}

        {!loading && error && (
          <Card className="border-red-500/60 bg-gradient-to-br from-red-900/70 to-red-950/80 shadow-[0_18px_40px_rgba(239,68,68,0.35)] backdrop-blur">
            <CardHeader>
              <CardTitle className="text-sm text-red-100">
                Error loading metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-red-100 break-all">{error}</p>
              <p className="mt-2 text-[11px] text-red-200/80">
                Check that the API is running and CORS allows{" "}
                <span className="font-mono">http://localhost:3000</span>.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Main metric surface */}
        {!loading && !error && (
          <section className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,1.2fr)] xl:grid-cols-[minmax(0,4fr)_minmax(0,1.2fr)]">
            {/* Primary metric panel */}
            <Card className="border border-slate-800/70 bg-gradient-to-br from-[#0d1529]/90 via-[#070d1c]/95 to-[#020409] shadow-[0_35px_90px_rgba(1,4,14,0.85)] backdrop-blur-xl">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-xs font-medium uppercase tracking-wide text-slate-300/90">
                  Traffic & cost
                  <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                    Live
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5 pt-1">
                <div className="grid gap-4 sm:grid-cols-4">
                  {/* Total runs */}
                  <div className="space-y-1">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">
                      Total runs
                    </p>
                    <p className="text-3xl font-semibold tabular-nums text-slate-50">
                      {totalRuns.toLocaleString()}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Since router startup
                    </p>
                  </div>

                  {/* Avg latency */}
                  <div className="space-y-1">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">
                      Avg latency
                    </p>
                    <p className="text-3xl font-semibold tabular-nums text-slate-50">
                      {avgLatency.toFixed(1)}
                      <span className="ml-1 text-base font-normal text-slate-400">
                        ms
                      </span>
                    </p>
                    <p className="text-[11px] text-slate-500">
                      End-to-end per run
                    </p>
                  </div>

                  {/* Total cost */}
                  <div className="space-y-1">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">
                      Total cost
                    </p>
                    <p className="text-2xl font-semibold tabular-nums text-emerald-300">
                      ${totalCost.toFixed(6)}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Sum of provider cost_usd
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
                  <MetricCard
                    label="Cost per run"
                    value={`$${costPerRun.toFixed(6)}`}
                    sublabel="This becomes powerful once OpenAI / Anthropic adapters return real usage costs."
                    valueClassName="text-base font-semibold text-slate-50 sm:text-lg"
                  />
                  <MetricCard
                    label="Router signal"
                    value="Live stream"
                    sublabel="Latency, provider cost, and category tags for each request."
                    valueClassName="text-base font-semibold text-cyan-200 sm:text-lg"
                  >
                    <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-900">
                      <div className="h-full w-2/3 bg-gradient-to-r from-emerald-400 via-cyan-400 to-sky-400" />
                    </div>
                  </MetricCard>
                  <MetricCard
                    label="Savings vs baseline (all gpt-4o)"
                    value={savingsDisplay}
                    sublabel="Compared to routing 100% of traffic through gpt-4o."
                    valueClassName="text-base font-semibold text-emerald-300 sm:text-lg"
                  />
                  <MetricCard
                    label="What-if GPT-4.1 (est)"
                    value={whatIfCost != null ? `$${whatIfCost.toFixed(6)}` : "—"}
                    sublabel="vs actual"
                    valueClassName="text-base font-semibold text-slate-50 sm:text-lg"
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <MetricCard
                    label="Avg ALRI (0–10)"
                    value={avgAlriScore != null ? avgAlriScore.toFixed(1) : "—"}
                    sublabel="ALRI summarizes cost, complexity, and safety pressure for your AI traffic."
                    valueClassName="text-2xl font-semibold text-slate-50"
                  />
                  <MetricCard
                    label="High ALRI runs"
                    value={highAlriDisplay}
                    sublabel="Share of requests that fall into long-retention / audit-grade tiers (orange or red)."
                    valueClassName="text-2xl font-semibold text-amber-300"
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="border border-slate-800/60 bg-gradient-to-br from-[#0b0f1d]/90 via-[#090d17]/85 to-[#04060c] shadow-[0_25px_70px_rgba(1,4,12,0.85)] backdrop-blur-lg">
              <CardHeader className="pb-1">
                <CardTitle className="text-sm font-medium text-slate-100">
                  How to use this view
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs leading-relaxed text-slate-200/90">
                <p>
                  <span className="font-semibold text-slate-50">Total runs</span>{" "}
                  tells you how much traffic actually flows through your smart
                  router instead of hitting a single model directly.
                </p>
                <p>
                  <span className="font-semibold text-slate-50">Avg latency</span>{" "}
                  is how fast the system feels to your agents, orchestrators, or
                  end-users.
                </p>
                <p>
                  <span className="font-semibold text-slate-50">Total cost</span>{" "}
                  will become the anchor for showing savings once multi-provider
                  adapters are fully enabled.
                </p>
                <p className="pt-2 text-[11px] text-slate-500">
                  This is intentionally lean but polished — a premium-looking
                  alpha view you can screenshot for early decks, while the
                  backend metrics model matures.
                </p>
              </CardContent>
            </Card>
          </section>
        )}

        {/* Empty state */}
        {!loading && !error && summary && summary.total_runs === 0 && (
          <p className="text-[11px] text-slate-500">
            No runs recorded yet. Trigger a call to{" "}
            <span className="font-mono text-slate-200">/v1/run</span> from the
            API docs, then refresh this page.
          </p>
        )}

        {summary && (
          <section className="mt-6 space-y-3">
            <h2 className="text-sm font-semibold tracking-wide text-slate-200">
              Provider breakdown
            </h2>
            {summary.provider_breakdown.length === 0 ? (
              <p className="text-xs text-slate-500">
                No routed runs recorded yet. Send some traffic through the router
                and refresh this page.
              </p>
            ) : (
              <div className="overflow-hidden rounded-2xl border border-slate-800/80 bg-gradient-to-br from-slate-900/70 to-slate-950/80 shadow-[0_25px_60px_rgba(1,3,10,0.75)]">
                <table className="min-w-full text-xs">
                  <thead className="bg-slate-900/70">
                    <tr className="text-left text-slate-400">
                      <th className="px-4 py-3 font-medium">Provider</th>
                      <th className="px-4 py-3 font-medium">Runs</th>
                      <th className="px-4 py-3 font-medium">Total cost</th>
                      <th className="px-4 py-3 font-medium">Avg latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.provider_breakdown.map((p) => (
                      <tr
                        key={p.provider}
                        className="border-t border-slate-800/70 text-slate-100"
                      >
                        <td className="px-4 py-3">
                          <ProviderBadge provider={p.provider} />
                        </td>
                        <td className="px-4 py-3">
                          {p.runs.toLocaleString()}
                        </td>
                        <td className="px-4 py-3">
                          ${p.total_cost_usd.toFixed(6)}
                        </td>
                        <td className="px-4 py-3">
                          {p.avg_latency_ms.toFixed(1)} ms
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
