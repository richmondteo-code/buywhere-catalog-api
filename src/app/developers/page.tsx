import type { Metadata } from "next";
import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Developer Portal — BuyWhere MCP Server & Product Catalog API for AI Agents",
  description:
    "Give your AI agent a live product catalog: search 5M+ products across Singapore retailers, compare prices, and generate purchase links — no scrapers, no maintenance. MCP server + REST API.",
  alternates: {
    canonical: "https://buywhere.ai/developers",
  },
};

const mcpConfig = `{
  "mcpServers": {
    "buywhere": {
      "command": "npx",
      "args": ["-y", "@buywhere/mcp-server"],
      "env": {
        "BUYWHERE_API_KEY": "bw_live_your_key_here"
      }
    }
  }
}`;

const curlExample = `curl -sS "https://api.buywhere.ai/v1/products/search?q=wireless+headphones&limit=5" \\
  -H "Authorization: Bearer bw_live_your_key_here"`;

export default function DevelopersPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Nav />

      <section className="border-b border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.15),_transparent_40%),linear-gradient(135deg,#0f172a_0%,#1e1b4b_100%)] text-white">
        <div className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.15em] text-indigo-200">
            Developer Portal
          </div>
          <h1 className="max-w-3xl text-4xl font-bold leading-tight sm:text-5xl">
            Ship product search in your AI agent — live catalog, no scraping.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-slate-300">
            BuyWhere gives AI agents a live product catalog layer: search 5M+ products across Singapore retailers, compare prices, and generate purchase links — all via one API call. MCP server included.
          </p>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-400">
            No scrapers. No maintenance. No HTML parsing. One authenticated request replaces real-time product data from every major SG retailer.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/api-keys"
              className="inline-flex items-center justify-center rounded-xl bg-white px-5 py-3 text-sm font-semibold text-indigo-700 transition-colors hover:bg-slate-100"
            >
              Get API key
            </Link>
            <Link
              href="/quickstart"
              className="inline-flex items-center justify-center rounded-xl border border-white/20 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              See 5-minute quickstart
            </Link>
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-slate-50 py-16">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 sm:px-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">REST API</p>
            <h2 className="mt-3 text-2xl font-bold text-slate-900">Canonical onboarding endpoint</h2>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              The shortest path to activation is one authenticated request to <code className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-900">GET https://api.buywhere.ai/v1/products/search</code>.
            </p>
            <div className="mt-6 overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
              <pre className="overflow-x-auto p-4 text-sm leading-6 text-gray-100">
                <code>{curlExample}</code>
              </pre>
            </div>
          </div>

          <div className="rounded-3xl border border-indigo-200 bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">MCP package</p>
            <h2 className="mt-3 text-2xl font-bold text-slate-900">Package-based MCP setup</h2>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              Use the published MCP package instead of the hosted MCP URL on public onboarding surfaces.
            </p>
            <div className="mt-6 overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
              <pre className="overflow-x-auto p-4 text-sm leading-6 text-gray-100">
                <code>{mcpConfig}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Link href="/api-keys" className="rounded-2xl border border-slate-200 bg-slate-50 p-6 transition-colors hover:border-indigo-200 hover:bg-indigo-50">
              <p className="text-sm font-semibold text-slate-900">1. Get API key</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">Create a working key instantly with the self-serve flow.</p>
            </Link>
            <Link href="/quickstart" className="rounded-2xl border border-slate-200 bg-slate-50 p-6 transition-colors hover:border-indigo-200 hover:bg-indigo-50">
              <p className="text-sm font-semibold text-slate-900">2. Follow quickstart</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">Run your first search request, then branch into the right integration path.</p>
            </Link>
            <Link href="/integrate" className="rounded-2xl border border-slate-200 bg-slate-50 p-6 transition-colors hover:border-indigo-200 hover:bg-indigo-50">
              <p className="text-sm font-semibold text-slate-900">3. Add MCP</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">Use the package-based MCP setup for Claude Desktop, Cursor, and custom agents.</p>
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
