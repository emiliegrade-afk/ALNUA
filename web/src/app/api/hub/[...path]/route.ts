import { NextRequest, NextResponse } from "next/server";

import { hubBackendBaseUrl } from "@/lib/hub-api-config";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

function resolveHubApiKey(): string {
  return process.env.HUB_API_KEY?.trim() || "";
}

async function proxyHubRequest(
  req: NextRequest,
  pathSegments: string[]
): Promise<NextResponse> {
  const hubKey = resolveHubApiKey();

  const backend = hubBackendBaseUrl();
  const target = new URL(`${backend}/${pathSegments.join("/")}`);
  req.nextUrl.searchParams.forEach((value, name) => {
    target.searchParams.append(name, value);
  });

  const headers = new Headers();
  req.headers.forEach((value, name) => {
    const lower = name.toLowerCase();
    if (HOP_BY_HOP.has(lower) || lower === "x-hub-key") {
      return;
    }
    headers.set(name, value);
  });
  // Dev open mode: backend accepts requests without X-Hub-Key when HUB_API_KEY is unset.
  if (hubKey) {
    headers.set("X-Hub-Key", hubKey);
  }

  const init: RequestInit = {
    method: req.method,
    headers,
    cache: "no-store",
    redirect: "manual",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  let upstream: Response;
  const timeoutMs = pathSegments[0] === "health" || pathSegments[0] === "status" ? 15_000 : 600_000;
  try {
    upstream = await fetch(target, { ...init, signal: AbortSignal.timeout(timeoutMs) });
  } catch {
    return NextResponse.json(
      { detail: "Backend Hub inaccessible (uvicorn sur le port 8000 ?)" },
      { status: 502 }
    );
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, name) => {
    if (!HOP_BY_HOP.has(name.toLowerCase())) {
      responseHeaders.set(name, value);
    }
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

type RouteContext = { params: { path: string[] } };

async function handle(
  req: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  return proxyHubRequest(req, context.params.path);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
