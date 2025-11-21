"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE =
  process.env.NEXT_PUBLIC_AGENTICLABS_API ?? "http://localhost:8000";

type MetricsSummary = {
  total_runs: number;
  avg_latency_ms: number;
  total_cost_usd: number;
};

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
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
        setMetrics(data);
      } catch (err: any) {
        console.error("Failed to load metrics:", err);
        setError(err?.message ?? "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, []);

  const totalRuns = metrics?.total_runs ?? 0;
  const avgLatency = metrics?.avg_latency_ms ?? 0;
  const totalCost = metrics?.total_cost_usd ?? 0;
  const costPerRun = totalRuns > 0 ? totalCost / totalRuns : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      {/* subtle gradient wash */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,_rgba(45,212,191,0.24),_transparent_55%),radial-gradient(circle_at_bottom,_rgba(56,189,248,0.16),_transparent_55%)] opacity-70" />
      <main className="relative mx-auto flex max-w-6xl flex-col gap-8 px-4 pb-16 pt-10 sm:px-6 lg:px-8">
        {/* Hero */}
        <section className="space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-slate-950/80 px-3 py-1 text-[11px] font-medium text-emerald-200 shadow-[0_0_0_1px_rgba(15,23,42,0.8)] backdrop-blur">
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
          <div className="rounded-2xl border border-slate-800/80 bg-slate-950/80 px-4 py-3 text-sm text-slate-200 backdrop-blur">
            Loading metrics…
          </div>
        )}

        {!loading && error && (
          <Card className="border-red-500/50 bg-red-950/70 backdrop-blur">
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
          <section className="grid gap-5 lg:grid-cols-[1.8fr,1.2fr]">
            {/* Primary metric panel */}
            <Card className="border-slate-800/80 bg-slate-950/80 shadow-[0_18px_45px_rgba(15,23,42,0.9)] backdrop-blur">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-xs font-medium uppercase tracking-wide text-slate-300/90">
                  Traffic & cost
                  <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                    Live
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5 pt-1">
                <div className="grid gap-4 sm:grid-cols-3">
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
                    <p className="text-3xl font-semibold tabular-nums text-emerald-300">
                      ${totalCost.toFixed(6)}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Sum of provider cost_usd
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {/* Cost per run */}
                  <div className="rounded-xl border border-slate-800/70 bg-slate-950/80 px-4 py-3">
                    <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
                      Cost per run
                    </p>
                    <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-50">
                      ${costPerRun.toFixed(6)}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-500">
                      This becomes powerful once OpenAI / Anthropic adapters
                      return real usage costs.
                    </p>
                  </div>

                  {/* Tiny “trend” stub */}
                  <div className="rounded-xl border border-slate-800/70 bg-slate-950/80 px-4 py-3">
                    <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
                      Router signal
                    </p>
                    <p className="mt-1 text-[13px] text-slate-200">
                      The router is already logging latency and provider cost.
                      Next steps: baseline vs actual cost and per-provider
                      breakdown for concrete savings stories.
                    </p>
                    <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-900">
                      <div className="h-full w-2/3 bg-gradient-to-r from-emerald-400 via-cyan-400 to-sky-400" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Right-hand “explainer” / product copy */}
            <Card className="border-slate-800/70 bg-slate-950/75 backdrop-blur">
              <CardHeader className="pb-1">
                <CardTitle className="text-sm font-medium text-slate-100">
                  How to use this view
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs leading-relaxed text-slate-200/90">
                <p>
                  <span className="font-semibold text-slate-50">
                    Total runs
                  </span>{" "}
                  tells you how much traffic actually flows through your smart
                  router instead of hitting a single model directly.
                </p>
                <p>
                  <span className="font-semibold text-slate-50">
                    Avg latency
                  </span>{" "}
                  is how fast the system feels to your agents, orchestration
                  layer, or end-users.
                </p>
                <p>
                  <span className="font-semibold text-slate-50">
                    Total cost
                  </span>{" "}
                  will become the anchor for showing savings once multi-provider
                  adapters (OpenAI, Anthropic, Ollama) are all enabled.
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
        {!loading && !error && metrics && metrics.total_runs === 0 && (
          <p className="text-[11px] text-slate-500">
            No runs recorded yet. Trigger a call to{" "}
            <span className="font-mono text-slate-200">/v1/run</span> from the
            API docs, then refresh this page.
          </p>
        )}
      </main>
    </div>
  );
}
