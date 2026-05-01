import type { Metadata } from "next";
import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "BuyWhere Integration Guide — MCP Server & API for AI Agents",
  description:
    "Connect BuyWhere to your AI agent in minutes. Use the MCP server to give your agent product search, price comparison, and deal discovery across Singapore and the US.",
  alternates: {
    canonical: "https://buywhere.ai/integrate",
  },
};

const mcpTools = [
  {
    name: "search_products",
    description:
      "Search the BuyWhere catalog by keyword. Returns ranked results from Lazada, Shopee, Qoo10, and Carousell with price, platform, and affiliate links.",
    exampleSg: "search_products(query='mechanical keyboard', region='sg', limit=5)",
    exampleUs: "search_products(query='mechanical keyboard', region='us', currency='USD', limit=5)",
    status: "live",
  },
  {
    name: "compare_prices",
    description:
      "Search for a product and return results sorted by price ascending — perfect for finding the best deal across all Singapore platforms.",
    exampleSg: "compare_prices(query='iphone 15 case', region='sg', limit=10)",
    exampleUs: "compare_prices(query='iphone 15 case', region='us', currency='USD', limit=10)",
    status: "live",
  },
  {
    name: "get_deals",
    description:
      "Find products with significant price drops. Returns current price, original price, and discount percentage sorted by savings.",
    exampleSg: "get_deals(category='electronics', region='sg', min_discount_pct=20)",
    exampleUs: "get_deals(category='electronics', region='us', currency='USD', min_discount_pct=20)",
    status: "preview",
  },
  {
    name: "find_deals",
    description:
      "Find the best current deals across platforms sorted by discount percentage. Includes expiration dates when available.",
    exampleSg: "find_deals(category='fashion', region='sg', minDiscount=30)",
    exampleUs: "find_deals(category='fashion', region='us', currency='USD', minDiscount=30)",
    status: "preview",
  },
  {
    name: "get_product",
    description:
      "Retrieve full details for a specific product by its BuyWhere ID — useful when you have a product ID from a previous search.",
    exampleSg: "get_product(product_id='bw_sg_12345', region='sg')",
    exampleUs: "get_product(product_id='bw_us_12345', region='us', currency='USD')",
    status: "live",
  },
  {
    name: "browse_categories",
    description:
      "Browse the BuyWhere category taxonomy tree to understand what product categories are available in the catalog.",
    exampleSg: "browse_categories(region='sg')",
    exampleUs: "browse_categories(region='us')",
    status: "live",
  },
  {
    name: "get_category_products",
    description:
      "Get paginated product listings within a specific category. Use browse_categories first to find the right categoryId.",
    exampleSg: "get_category_products(category_id='electronics', region='sg', limit=20)",
    exampleUs: "get_category_products(category_id='electronics', region='us', currency='USD', limit=20)",
    status: "live",
  },
];

const examplePrompts = [
  {
    title: "Best-price lookup",
    description:
      "Your agent finds the cheapest option for a product across all Singapore platforms.",
    prompt:
      "Find the best price for a Sony WH-1000XM5 wireless headphone across Singapore shops. Show me where to buy it cheapest and include the affiliate link.",
    tools: ["search_products", "compare_prices"],
  },
  {
    title: "Deal discovery",
    description:
      "Your agent surfaces current deals in a category, sorted by discount.",
    prompt:
      "Show me the best tech deals available right now in Singapore — at least 30% off. List them with original price, sale price, and where to buy.",
    tools: ["get_deals", "find_deals"],
  },
  {
    title: "Product search & comparison",
    description:
      "Your agent searches for products and presents options with key details.",
    prompt:
      "I need a birthday gift for my brother — something under $50. Find popular wireless earbuds available in Singapore with prices and links.",
    tools: ["search_products", "compare_prices"],
  },
  {
    title: "Category browsing",
    description: "Your agent explores what categories and products are available.",
    prompt:
      "What product categories does BuyWhere have? I'm looking to browse home appliances.",
    tools: ["browse_categories", "get_category_products"],
  },
];

const setupSteps = [
  {
    step: "1",
    title: "Get a BuyWhere API key",
    description:
      "Sign up at buywhere.ai/api-keys to get an instant beta key. No credit card required.",
    cta: "Get API key",
    ctaHref: "/api-keys",
  },
  {
    step: "2",
    title: "Configure the MCP server",
    description:
      "Point the MCP server to your API key and the BuyWhere API URL. The server runs locally on your machine.",
    cta: "View setup guide",
    ctaHref: "/quickstart#connect-mcp",
  },
  {
    step: "3",
    title: "Connect to your agent",
    description:
      "Add BuyWhere to your MCP-compatible agent: Claude Desktop, Cursor, or any other MCP client.",
    cta: "See example configs",
    ctaHref: "/quickstart",
  },
];

export default function IntegratePage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Nav />

      <section className="border-b border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.12),_transparent_40%),linear-gradient(135deg,#0f172a_0%,#1e1b4b_100%)] text-white">
        <div className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
          <div className="max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.15em] text-indigo-200">
              MCP Server + REST API
            </div>
            <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
              Give your AI agent a product catalog layer for Singapore commerce.
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-slate-300">
              BuyWhere exposes product search, price comparison, and deal discovery
              as tools your agent can call directly — no scraping, no HTML parsing,
              no rate-limit battles with e-commerce sites.
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
                View quickstart
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-slate-50 py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mb-12 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
              MCP tools
            </p>
            <h2 className="mt-3 text-3xl font-bold text-slate-900">
              7 tools available via MCP
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-slate-600">
              Each tool maps to a BuyWhere API endpoint. The MCP server handles
              authentication and returns formatted text your agent can reason over.{" "}
              <span className="font-medium text-slate-700">
                Singapore tools are live; US catalog is in preview.
              </span>
            </p>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            {mcpTools.map((tool) => (
              <div
                key={tool.name}
                className="rounded-2xl border border-slate-200 bg-white p-6"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-mono text-sm font-semibold text-indigo-600">
                      {tool.name}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-600">
                      {tool.description}
                    </p>
                  </div>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    tool.status === 'live'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-amber-100 text-amber-700'
                  }`}>
                    {tool.status === 'live' ? 'Live' : 'Preview'}
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  <div className="rounded-xl bg-slate-950 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="inline-flex items-center rounded-full bg-green-900/40 px-2 py-0.5 text-xs font-medium text-green-400">SG — Live</span>
                    </div>
                    <p className="font-mono text-xs text-slate-300">{tool.exampleSg}</p>
                  </div>
                  <div className="rounded-xl bg-slate-900 border border-amber-800/30 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="inline-flex items-center rounded-full bg-amber-900/40 px-2 py-0.5 text-xs font-medium text-amber-400">US — Preview</span>
                    </div>
                    <p className="font-mono text-xs text-slate-300">{tool.exampleUs}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-white py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mb-12 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
              Example prompts
            </p>
            <h2 className="mt-3 text-3xl font-bold text-slate-900">
              Prompt your agent to use BuyWhere tools
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-slate-600">
              Copy these prompts into your agent workflow. Each one triggers one or
              more BuyWhere MCP tools.
            </p>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            {examplePrompts.map((prompt) => (
              <div
                key={prompt.title}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-6"
              >
                <h3 className="text-lg font-semibold text-slate-900">
                  {prompt.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  {prompt.description}
                </p>
                <div className="mt-4 rounded-xl bg-white border border-slate-200 p-4">
                  <p className="text-sm italic leading-relaxed text-slate-700">
                    &ldquo;{prompt.prompt}&rdquo;
                  </p>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {prompt.tools.map((tool) => (
                    <span
                      key={tool}
                      className="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-slate-50 py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mb-12 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
              Setup
            </p>
            <h2 className="mt-3 text-3xl font-bold text-slate-900">
              Get started in three steps
            </h2>
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            {setupSteps.map((step) => (
              <div
                key={step.step}
                className="rounded-2xl border border-slate-200 bg-white p-6"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white font-bold">
                  {step.step}
                </div>
                <h3 className="mt-4 text-lg font-semibold text-slate-900">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  {step.description}
                </p>
                <Link
                  href={step.ctaHref}
                  className="mt-4 inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-700"
                >
                  {step.cta} →
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-indigo-600 py-20 text-white">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="text-3xl font-bold">
            Ready to power your agent with product data?
          </h2>
          <p className="mt-4 text-lg text-indigo-200">
            Get an API key and start building. The MCP server is live and ready for
            agent workflows today.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/api-keys"
              className="inline-flex items-center justify-center rounded-xl bg-white px-6 py-3 text-sm font-semibold text-indigo-700 transition-colors hover:bg-indigo-50"
            >
              Get API key
            </Link>
            <Link
              href="/quickstart"
              className="inline-flex items-center justify-center rounded-xl border border-indigo-400 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
            >
              View full quickstart
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}