"use client";

import { useState } from "react";

type ProviderKey = "auto" | "openai" | "anthropic" | "grok" | "gemini" | "ollama";
type LayoutMode = "classic-chat" | "split-right" | "stacked" | "console";

interface ProviderTheme {
  label: string;
  layout: LayoutMode;
  accentClass: string;
  backgroundClass: string;
  chipClass: string;
}

const PROVIDER_THEMES: Record<ProviderKey, ProviderTheme> = {
  auto: {
    label: "Auto (Router decides)",
    layout: "classic-chat",
    accentClass: "border-indigo-400",
    backgroundClass:
      "bg-[radial-gradient(circle_at_top,_rgba(79,70,229,0.2),_transparent_52%),radial-gradient(circle_at_bottom,_rgba(15,118,110,0.18),_transparent_55%),#020617]",
    chipClass: "bg-slate-800 text-slate-200",
  },
  openai: {
    label: "GPT (OpenAI)",
    layout: "split-right",
    accentClass: "border-[#74AA9C]",
    backgroundClass:
      "bg-gradient-to-br from-[#0c1f1a] via-[#082820] to-[#031410]",
    chipClass: "bg-[#1d3f34] text-[#9fd6c7]",
  },
  anthropic: {
    label: "Claude (Anthropic)",
    layout: "stacked",
    accentClass: "border-amber-300",
    backgroundClass:
      "bg-gradient-to-br from-[#3d1d05] via-[#4e2a0d] to-[#1d1006]",
    chipClass: "bg-[#5c3411] text-[#ffd7a3]",
  },
  grok: {
    label: "Grok",
    layout: "console",
    accentClass: "border-white/70",
    backgroundClass:
    "bg-gradient-to-br from-black via-[#0f0f0f] to-black",
    chipClass: "bg-white/10 text-white",
  },
  gemini: {
    label: "Gemini",
    layout: "split-right",
    accentClass: "border-sky-400",
    backgroundClass:
      "bg-[radial-gradient(circle_at_top_left,_rgba(239,68,68,0.25),_transparent_35%),radial-gradient(circle_at_top_right,_rgba(59,130,246,0.3),_transparent_40%),radial-gradient(circle_at_bottom_left,_rgba(250,204,21,0.25),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(34,197,94,0.3),_transparent_40%),#03050f]",
    chipClass: "bg-[#113472] text-sky-200",
  },
  ollama: {
    label: "Ollama (Local)",
    layout: "classic-chat",
    accentClass: "border-blue-300",
    backgroundClass:
      "bg-gradient-to-br from-[#07142a] via-[#0b223f] to-[#02060d]",
    chipClass: "bg-[#0f356b] text-blue-100",
  },
};

interface RouterResult {
  output: string;
  provider: string;
  model: string;
  band: string;
  latency_ms?: number;
  cost?: {
    total_usd?: number;
    input_usd?: number;
    output_usd?: number;
  };
  usage?: {
    input_tokens?: number | null;
    output_tokens?: number | null;
    total_tokens?: number | null;
  } | null;
  debug?: any;
}

type BandChoice = "auto" | "low" | "medium" | "high";

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState("");
  const [band, setBand] = useState<BandChoice>("auto");
  const [selectedProvider, setSelectedProvider] = useState<ProviderKey>("auto");
  const [routerMode, setRouterMode] = useState<"baseline" | "enhanced">(
    "baseline",
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RouterResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"response" | "trace" | "cost">(
    "response",
  );

  const providerKeyFromResult =
    (result?.provider?.toLowerCase() as ProviderKey) || "auto";
  const theme =
    selectedProvider === "auto"
      ? PROVIDER_THEMES[providerKeyFromResult] || PROVIDER_THEMES.auto
      : PROVIDER_THEMES[selectedProvider];

  async function handleRun() {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);

      try {
        const payload: Record<string, any> = {
          prompt,
          router_mode: routerMode,
          force_provider: selectedProvider === "auto" ? null : selectedProvider,
        };
        if (band !== "auto") {
          payload.band = band;
        }

        const res = await fetch("/api/router-proxy", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed: ${res.status}`);
      }

      const data = (await res.json()) as RouterResult;
      setResult(data);
      setActiveTab("response");
    } catch (e: any) {
      setError(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      className={cn(
        "flex min-h-screen flex-col text-slate-100",
        theme.backgroundClass,
      )}
    >
      <header className="flex items-center justify-between border-b border-slate-800/80 px-6 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm uppercase tracking-[0.2em] text-slate-500">
            AgenticLabs
          </span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
            Router Playground
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {result && (
            <span className={cn("rounded-full px-2 py-1", theme.chipClass)}>
              Routed to {result.provider ?? "?"} · {result.model ?? "unknown"}
            </span>
          )}
          {typeof result?.latency_ms === "number" && (
            <span className="rounded-full bg-slate-900 px-2 py-1 text-slate-300">
              {Math.round(result.latency_ms)} ms
            </span>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="flex w-72 flex-col gap-4 border-r border-slate-800/80 bg-slate-950/80 p-4">
          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Router Mode
            </h2>
            <div className="flex gap-2">
              {["baseline", "enhanced"].map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() =>
                    setRouterMode(mode as "baseline" | "enhanced")
                  }
                  className={cn(
                    "flex-1 rounded-md border px-2 py-1 text-xs capitalize transition",
                    routerMode === mode
                      ? "border-emerald-400 bg-emerald-500/10 text-emerald-200"
                      : "border-slate-700 bg-slate-950/60 text-slate-400 hover:bg-slate-900/60",
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Provider Mode
            </h2>
            <select
              value={selectedProvider}
              onChange={(e) =>
                setSelectedProvider(e.target.value as ProviderKey)
              }
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              {Object.entries(PROVIDER_THEMES).map(([key, cfg]) => (
                <option key={key} value={key}>
                  {cfg.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Band
            </h2>
            <div className="flex flex-wrap gap-2">
              {(["auto", "low", "medium", "high"] as BandChoice[]).map((b) => (
                <button
                  key={b}
                  type="button"
                  onClick={() => setBand(b)}
                  className={cn(
                    "flex-1 rounded-md border px-2 py-1 text-xs capitalize transition min-w-[70px]",
                    band === b
                      ? cn("bg-slate-900", theme.accentClass)
                      : "border-slate-700 bg-slate-950/60 hover:bg-slate-900/60",
                  )}
                >
                  {b === "auto" ? "Auto" : b}
                </button>
              ))}
            </div>
          </div>
          <div className="mt-auto text-[11px] text-slate-500">
            <p>Requests route through the AgenticLabs Smart Router.</p>
            <p>Use this page to test bands, providers & costs.</p>
          </div>
        </aside>

        <section className="flex-1 p-4">
          {theme.layout === "classic-chat" && (
            <ClassicChatLayout
              prompt={prompt}
              setPrompt={setPrompt}
              loading={loading}
              onRun={handleRun}
              result={result}
              error={error}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              theme={theme}
            />
          )}
          {theme.layout === "split-right" && (
            <SplitRightLayout
              prompt={prompt}
              setPrompt={setPrompt}
              loading={loading}
              onRun={handleRun}
              result={result}
              error={error}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              theme={theme}
            />
          )}
          {theme.layout === "stacked" && (
            <StackedLayout
              prompt={prompt}
              setPrompt={setPrompt}
              loading={loading}
              onRun={handleRun}
              result={result}
              error={error}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              theme={theme}
            />
          )}
          {theme.layout === "console" && (
            <ConsoleLayout
              prompt={prompt}
              setPrompt={setPrompt}
              loading={loading}
              onRun={handleRun}
              result={result}
              error={error}
              theme={theme}
            />
          )}
        </section>
      </div>
    </main>
  );
}

interface LayoutProps {
  prompt: string;
  setPrompt: (v: string) => void;
  loading: boolean;
  onRun: () => void;
  result: RouterResult | null;
  error: string | null;
  theme: ProviderTheme;
  activeTab?: "response" | "trace" | "cost";
  setActiveTab?: (tab: "response" | "trace" | "cost") => void;
}

function PromptBox({
  prompt,
  setPrompt,
  loading,
  onRun,
}: {
  prompt: string;
  setPrompt: (v: string) => void;
  loading: boolean;
  onRun: () => void;
}) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-950/80 p-3">
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Ask the router to do something…"
        className="min-h-[120px] w-full resize-none bg-transparent text-sm focus:outline-none"
      />
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-slate-500">
          Shift+Enter for newline · Enter to send
        </span>
        <button
          type="button"
          onClick={onRun}
          disabled={loading || !prompt.trim()}
          className={cn(
            "flex items-center gap-1 rounded-md border border-indigo-400/60 bg-indigo-500/10 px-3 py-1.5 text-xs font-medium hover:bg-indigo-500/20 disabled:opacity-40",
          )}
        >
          {loading ? "Routing…" : "Run through router"}
        </button>
      </div>
    </div>
  );
}

function ResponseTabs({
  result,
  error,
  activeTab,
  setActiveTab,
}: {
  result: RouterResult | null;
  error: string | null;
  activeTab?: "response" | "trace" | "cost";
  setActiveTab?: (tab: "response" | "trace" | "cost") => void;
}) {
  if (!activeTab || !setActiveTab) return null;

  return (
    <div className="mt-3 flex h-full flex-col rounded-xl border border-slate-800 bg-slate-950/80">
      <div className="flex border-b border-slate-800 text-xs">
        {["response", "trace", "cost"].map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab as "response" | "trace" | "cost")}
            className={cn(
              "px-3 py-2 capitalize",
              activeTab === tab
                ? "border-b border-indigo-400 text-indigo-300"
                : "text-slate-500",
            )}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-auto p-3 text-sm">
        {error && <p className="mb-2 text-xs text-red-400">Error: {error}</p>}
        {!result && !error && (
          <p className="text-xs text-slate-500">
            Run a request to see router output, trace & cost.
          </p>
        )}
        {result && activeTab === "response" && (
          <pre className="whitespace-pre-wrap">{result.output || "<no output>"}</pre>
        )}
        {result && activeTab === "trace" && (
          <pre className="whitespace-pre-wrap text-[11px] text-slate-300">
            {JSON.stringify(
              {
                provider: result.provider,
                model: result.model,
                band: result.band,
                usage: result.usage,
                debug: result.debug,
              },
              null,
              2,
            )}
          </pre>
        )}
        {result && activeTab === "cost" && (
          <div className="space-y-1 text-xs">
            <p>Total USD: {result.cost?.total_usd ?? "?"}</p>
            <p>Input USD: {result.cost?.input_usd ?? "?"}</p>
            <p>Output USD: {result.cost?.output_usd ?? "?"}</p>
            <p className="mt-2 text-slate-500">
              Tokens:{" "}
              {result.usage
                ? `${result.usage.total_tokens} (in: ${result.usage.input_tokens}, out: ${result.usage.output_tokens})`
                : "unknown"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function ClassicChatLayout(props: LayoutProps) {
  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col gap-3">
      <PromptBox {...props} />
      <ResponseTabs
        result={props.result}
        error={props.error}
        activeTab={props.activeTab}
        setActiveTab={props.setActiveTab}
      />
    </div>
  );
}

function SplitRightLayout(props: LayoutProps) {
  return (
    <div className="grid h-full grid-cols-2 gap-4">
      <div className="flex h-full flex-col">
        <PromptBox {...props} />
      </div>
      <div className="flex h-full flex-col">
        <ResponseTabs
          result={props.result}
          error={props.error}
          activeTab={props.activeTab}
          setActiveTab={props.setActiveTab}
        />
      </div>
    </div>
  );
}

function StackedLayout(props: LayoutProps) {
  return (
    <div className="flex h-full flex-col gap-3">
      <PromptBox {...props} />
      <ResponseTabs
        result={props.result}
        error={props.error}
        activeTab={props.activeTab}
        setActiveTab={props.setActiveTab}
      />
    </div>
  );
}

function ConsoleLayout(props: LayoutProps) {
  const { prompt, setPrompt, loading, onRun, result, error } = props;
  return (
    <div className="flex h-full flex-col gap-2 rounded-xl border border-slate-800 bg-black/90 p-3 font-mono text-xs">
      <div className="text-slate-400">$ agenticlabs router --interactive</div>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="> Type a command or prompt…"
        className="mt-2 min-h-[100px] w-full bg-transparent focus:outline-none"
      />
      <button
        type="button"
        onClick={onRun}
        disabled={loading || !prompt.trim()}
        className="mt-1 self-start rounded bg-slate-800 px-3 py-1 hover:bg-slate-700 disabled:opacity-40"
      >
        {loading ? "Running…" : "Execute"}
      </button>
      <div className="mt-2 flex-1 overflow-auto border-t border-slate-800 pt-2">
        {error && <div className="text-red-400">! {error}</div>}
        {!result && !error && (
          <div className="text-slate-500">
            # Output from router will appear here.
          </div>
        )}
        {result && (
          <pre className="whitespace-pre-wrap text-slate-200">
            {result.output || "<no output>"}

            {"\n\n"}# meta:
            {"\n"}provider: {result.provider}
            {"\n"}model: {result.model}
            {"\n"}band: {result.band}
          </pre>
        )}
      </div>
    </div>
  );
}

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}
