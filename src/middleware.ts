import { NextRequest, NextResponse } from "next/server";

// Discovery Link headers for AI agent / Cloudflare readiness
const DISCOVERY_LINK =
  '<https://buywhere.ai/llms.txt>; rel="describedby"; type="text/plain", ' +
  '<https://buywhere.ai/.well-known/api-catalog>; rel="service-desc"; type="application/json", ' +
  '<https://buywhere.ai/.well-known/mcp/server-card.json>; rel="service-desc"; type="application/json", ' +
  '<https://buywhere.ai/openapi.json>; rel="service-desc"; type="application/json"';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accept = request.headers.get("accept") ?? "";
  const wantsMarkdown = accept.includes("text/markdown");

  // Content negotiation: rewrite to dedicated markdown route handlers
  if (wantsMarkdown) {
    if (pathname === "/" || pathname === "") {
      return NextResponse.rewrite(new URL("/index.md", request.url));
    }
    if (pathname === "/docs" || pathname === "/docs/") {
      return NextResponse.rewrite(new URL("/docs-md", request.url));
    }
  }

  // Add discovery Link headers for HTML responses on / and /docs/
  const isDiscoveryRoute =
    pathname === "/" ||
    pathname === "" ||
    pathname === "/docs" ||
    pathname === "/docs/";

  if (isDiscoveryRoute) {
    const response = NextResponse.next();
    response.headers.set("Link", DISCOVERY_LINK);
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/docs", "/docs/"],
};
