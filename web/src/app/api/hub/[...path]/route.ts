import { NextRequest, NextResponse } from "next/server";

import { readFileSync, existsSync } from "fs";
import { join } from "path";

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

let cachedBackend: { url: string; at: number } | null = null;
const CACHE_MS = 60_000;

function resolveHubApiKey(): string {
  return process.env.HUB_API_KEY?.trim() || "";
}

function resolveBackendUrlSync(): string {
  const configured = process.env.HUB_API_BACKEND_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  try {
    const portFile = join(process.cwd(), "..", "data", "hub_active_port.txt");
    if (existsSync(portFile)) {
      const port = parseInt(
        readFileSync(portFile, "utf8").replace(/^\uFEFF/, "").trim(),
        10
      );
      if (port > 0) {
        return `http://127.0.0.1:${port}`;
      }
    }
  } catch {
    // fall through
  }
  return hubBackendBaseUrl();
}

async function resolveBackendUrl(): Promise<string> {
  const snapshot = cachedBackend;
  if (snapshot && Date.now() - snapshot.at < CACHE_MS) {
    return snapshot.url;
  }
  const url = resolveBackendUrlSync();
  cachedBackend = { url, at: Date.now() };
  return url;
}

function invalidateHubBackendCache(): void {
  cachedBackend = null;
}

async function proxyHubRequest(
  req: NextRequest,
  pathSegments: string[]
): Promise<NextResponse> {
  const hubKey = resolveHubApiKey();
  const backend = await resolveBackendUrl();
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

  const isLight =
    pathSegments[0] === "health" || pathSegments[0] === "status";
  const timeoutMs = isLight ? 25_000 : 600_000;

  try {
    const upstream = await fetch(target, {
      ...init,
      signal: AbortSignal.timeout(timeoutMs),
    });

    const responseHeaders = new Headers();
    upstream.headers.forEach((value, name) => {
      if (!HOP_BY_HOP.has(name.toLowerCase())) {
        responseHeaders.set(name, value);
      }
    });
    responseHeaders.set("X-Hub-Backend", backend);

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    invalidateHubBackendCache();
    return NextResponse.json(
      {
        detail: `Backend Hub inaccessible (${backend} — lance Demarrer-Hub.bat)`,
      },
      { status: 502 }
    );
  }
}

type RouteContext = { params: { path: string[] } };

async function handle(
  req: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  try {
    const segments = context.params?.path;
    if (!segments?.length) {
      return NextResponse.json({ detail: "Chemin API manquant" }, { status: 400 });
    }
    return await proxyHubRequest(req, segments);
  } catch (err) {
    invalidateHubBackendCache();
    console.error("[hub-proxy]", err);
    return NextResponse.json(
      { detail: "Proxy Hub indisponible — relance Demarrer-Hub.bat" },
      { status: 502 }
    );
  }
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
