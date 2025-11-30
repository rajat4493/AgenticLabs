import { NextResponse } from "next/server";

const API_BASE =
  process.env.AGENTICLABS_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://api:8000";

const BAND_MAP: Record<string, string> = {
  low: "simple",
  medium: "moderate",
  high: "complex",
};

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const prompt = body?.prompt;
    if (typeof prompt !== "string" || prompt.trim().length === 0) {
      return NextResponse.json(
        { error: "Prompt is required" },
        { status: 400 },
      );
    }

    const bandInput = typeof body?.band === "string" ? body.band : undefined;
    const mappedBand = bandInput ? BAND_MAP[bandInput] : undefined;
    const forceProvider =
      typeof body?.force_provider === "string" &&
      body.force_provider !== "auto"
        ? body.force_provider
        : undefined;

    const policy_overrides: Record<string, string> = {};
    if (mappedBand) {
      policy_overrides.force_band = mappedBand;
    }
    if (forceProvider) {
      policy_overrides.force_provider = forceProvider;
    }

    const routerMode =
      typeof body?.router_mode === "string" ? body.router_mode : undefined;

    const runPayload: Record<string, unknown> = {
      prompt,
      agent_id: body?.agent_id ?? "router-playground",
      context: body?.context ?? {},
    };
    if (Object.keys(policy_overrides).length > 0) {
      runPayload.policy_overrides = policy_overrides;
    }
    if (routerMode) {
      runPayload.router_mode = routerMode;
    }

    const apiRes = await fetch(`${API_BASE}/v1/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(runPayload),
    });

    if (!apiRes.ok) {
      const text = await apiRes.text();
      return NextResponse.json(
        {
          error:
            text || `Router request failed with status ${apiRes.status}`,
        },
        { status: apiRes.status },
      );
    }

    const data = await apiRes.json();
    const provider = data?.provenance?.provider ?? "unknown";
    const model = data?.provenance?.model ?? "unknown";
    const response = {
      output: data?.output ?? "",
      provider,
      model,
      band: mappedBand ?? "auto",
      latency_ms: data?.metrics?.latency_ms,
      cost: {
        total_usd: data?.metrics?.cost_usd,
      },
      usage: data?.metrics?.usage ?? null,
      debug: data,
    };
    return NextResponse.json(response);
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message ?? "Unexpected router proxy failure" },
      { status: 500 },
    );
  }
}
