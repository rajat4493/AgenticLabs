"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { TrendingUp, Wallet, Database, RefreshCw } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";

// ---------------------------------------------
// Types & Mock Data (falls back when API is down)
// ---------------------------------------------

type RangeKey = "24h" | "7d" | "30d";

type ProviderKey = "openai" | "anthropic" | "ollama" | "azure";

interface Totals {
  cost_usd: number;
  requests: number;
  tokens_in: number;
  tokens_out: number;
  cache_hits?: number;
  cache_hit_rate?: number; // 0..1
  avg_latency_ms?: number;
  savings_vs_baseline?: number; // positive = saved USD
}

interface ByDayItem {
  date: string; // YYYY-MM-DD
  cost_usd: number;
  requests: number;
  tokens_in: number;
  tokens_out: number;
}

interface ByProviderItem {
  provider: ProviderKey | string;
  cost_usd: number;
  requests: number;
}

interface ByModelItem {
  provider: ProviderKey | string;
  model: string;
  cost_usd: number;
  requests: number;
  unit_cost_per_1k_tokens?: number;
}

interface CostResponse {
  range: RangeKey;
  totals: Totals;
  by_day: ByDayItem[];
  by_provider: ByProviderItem[];
  by_model: ByModelItem[];
  generated_at: string; // ISO time
}

const MOCK: CostResponse = {
  range: "7d",
  totals: {
    cost_usd: 124.83,
    requests: 1823,
    tokens_in: 1_920_000,
    tokens_out: 2_410_000,
    cache_hits: 694,
    cache_hit_rate: 0.38,
    avg_latency_ms: 812,
    savings_vs_baseline: 96.4,
  },
  by_day: Array.from({ length: 7 }).map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    const cost = 12 + Math.random() * 8;
    return {
      date: d.toISOString().slice(0, 10),
      cost_usd: Number(cost.toFixed(2)),
      requests: 200 + Math.floor(Math.random() * 120),
      tokens_in: 200_000 + Math.floor(Math.random() * 80_000),
      tokens_out: 300_000 + Math.floor(Math.random() * 120_000),
    };
  }),
  by_provider: [
    { provider: "openai", cost_usd: 72.4, requests: 884 },
    { provider: "anthropic", cost_usd: 31.1, requests: 521 },
    { provider: "ollama", cost_usd: 0.0, requests: 342 },
    { provider: "azure", cost_usd: 21.3, requests: 76 },
  ],
  by_model: [
    { provider: "openai", model: "gpt-4o-mini", cost_usd: 28.2, requests: 481, unit_cost_per_1k_tokens: 0.6 },
    { provider: "openai", model: "o4-mini", cost_usd: 44.2, requests: 403, unit_cost_per_1k_tokens: 1.2 },
    { provider: "anthropic", model: "claude-3.5-sonnet", cost_usd: 24.5, requests: 298, unit_cost_per_1k_tokens: 1.4 },
    { provider: "anthropic", model: "claude-3.5-haiku", cost_usd: 6.6, requests: 223, unit_cost_per_1k_tokens: 0.4 },
    { provider: "ollama", model: "llama3.1:8b-instruct", cost_usd: 0, requests: 342, unit_cost_per_1k_tokens: 0 },
    { provider: "azure", model: "gpt-4o-mini-azure", cost_usd: 21.3, requests: 76, unit_cost_per_1k_tokens: 1.1 },
  ],
  generated_at: new Date().toISOString(),
};

// ---------------------------------------------
// Fetch hook (uses API if available, otherwise MOCK)
// ---------------------------------------------

function useCosts(range: RangeKey) {
  const [data, setData] = React.useState<CostResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Prefer the AgenticLabs FastAPI endpoint if available
      const url = `/api/metrics/costs?range=${range}`; // Next.js route (proxy to FastAPI) or direct FastAPI if you map it
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as CostResponse;
      setData(json);
    } catch (e: any) {
      // Fallback to mock for local development
      console.warn("/api/metrics/costs unavailable, using mock:", e?.message);
      const mock = { ...MOCK, range };
      setData(mock);
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, [range]);

  React.useEffect(() => {
    load();
  }, [load]);

  return { data, error, loading, reload: load };
}

// ---------------------------------------------
// Small UI helpers
// ---------------------------------------------

function k(x: number) {
  if (x >= 1_000_000) return (x / 1_000_000).toFixed(1) + "M";
  if (x >= 1_000) return (x / 1_000).toFixed(1) + "k";
  return x.toFixed(0);
}

function usd(x: number) {
  return `$${x.toFixed(2)}`;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: "#6366f1",
  anthropic: "#22c55e",
  ollama: "#a3a3a3",
  azure: "#0ea5e9",
};

// ---------------------------------------------
// Main Page Component
// ---------------------------------------------

export default function OverviewPage() {
  const [range, setRange] = React.useState<RangeKey>("7d");
  const { data, error, loading, reload } = useCosts(range);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Cost Dashboard</h1>
          <p className="text-sm text-muted-foreground">Live view of spend, usage, and savings across providers.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={range} onValueChange={(v) => setRange(v as RangeKey)}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7d</SelectItem>
              <SelectItem value="30d">Last 30d</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={reload}>
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Could not load live metrics</AlertTitle>
          <AlertDescription>
            Falling back to mock data for development. Check your FastAPI <code>/metrics/costs</code> endpoint.
          </AlertDescription>
        </Alert>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))
        ) : (
          <>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Spend</CardTitle>
              </CardHeader>
              <CardContent className="flex items-end justify-between">
                <div className="text-3xl font-semibold">{usd(data!.totals.cost_usd)}</div>
                <Wallet className="w-6 h-6 text-muted-foreground" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Requests</CardTitle>
              </CardHeader>
              <CardContent className="flex items-end justify-between">
                <div className="text-3xl font-semibold">{k(data!.totals.requests)}</div>
                <TrendingUp className="w-6 h-6 text-muted-foreground" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Tokens (In → Out)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-semibold">
                  {k(data!.totals.tokens_in)} → {k(data!.totals.tokens_out)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Aggregated over range</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Savings vs Baseline</CardTitle>
              </CardHeader>
              <CardContent className="flex items-end justify-between">
                <div className="text-3xl font-semibold">{usd(Math.max(0, data!.totals.savings_vs_baseline || 0))}</div>
                <Database className="w-6 h-6 text-muted-foreground" />
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        {/* Daily Spend */}
        <Card className="xl:col-span-3">
          <CardHeader>
            <CardTitle>Daily Spend</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {loading ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data!.by_day} margin={{ left: 12, right: 12, top: 10, bottom: 10 }}>
                  <XAxis dataKey="date" tickLine={false} axisLine={false} />
                  <YAxis tickFormatter={(v) => `$${v}`} tickLine={false} axisLine={false} />
                  <Tooltip formatter={(v: any) => [`$${Number(v).toFixed(2)}`, "Spend"]} />
                  <Line type="monotone" dataKey="cost_usd" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Provider Share */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Spend by Provider</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {loading ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data!.by_provider}
                    dataKey="cost_usd"
                    nameKey="provider"
                    cx="50%"
                    cy="50%"
                    outerRadius={86}
                    label={(entry: any) => `${entry.payload.provider} ${(entry.percent * 100).toFixed(0)}%`}
                  >
                    {data!.by_provider.map((p, i) => (
                      <Cell key={i} fill={PROVIDER_COLORS[p.provider] || "#64748b"} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: any, _n: any, p: any) => [`$${Number(v).toFixed(2)}`, p?.payload?.provider]} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Models Table + Bar */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        {/* Bar by Provider */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Requests by Provider</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {loading ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data!.by_provider} margin={{ left: 12, right: 12, top: 10, bottom: 10 }}>
                  <XAxis dataKey="provider" tickLine={false} axisLine={false} />
                  <YAxis tickFormatter={(v) => `${v}`} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Bar dataKey="requests">
                    {data!.by_provider.map((p, i) => (
                      <Cell key={i} fill={PROVIDER_COLORS[p.provider] || "#64748b"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Models Table */}
        <Card className="xl:col-span-3">
          <CardHeader>
            <CardTitle>Top Models (by spend)</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-muted-foreground">
                      <th className="py-2 pr-4">Provider</th>
                      <th className="py-2 pr-4">Model</th>
                      <th className="py-2 pr-4">Requests</th>
                      <th className="py-2 pr-4">Spend</th>
                      <th className="py-2 pr-4">$/1k tokens</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data!.by_model
                      .slice()
                      .sort((a, b) => b.cost_usd - a.cost_usd)
                      .map((m, idx) => (
                        <tr key={idx} className="border-t border-border/50">
                          <td className="py-2 pr-4 capitalize flex items-center gap-2">
                            <span
                              className="inline-block h-2.5 w-2.5 rounded-full"
                              style={{ background: PROVIDER_COLORS[m.provider] || "#64748b" }}
                            />
                            {m.provider}
                          </td>
                          <td className="py-2 pr-4 font-medium">{m.model}</td>
                          <td className="py-2 pr-4">{k(m.requests)}</td>
                          <td className="py-2 pr-4">{usd(m.cost_usd)}</td>
                          <td className="py-2 pr-4">{m.unit_cost_per_1k_tokens != null ? `$${m.unit_cost_per_1k_tokens.toFixed(2)}` : "—"}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Footer / Generated at */}
      {!loading && (
        <p className="text-xs text-muted-foreground text-right">Updated: {new Date(data!.generated_at).toLocaleString()}</p>
      )}
    </div>
  );
}
