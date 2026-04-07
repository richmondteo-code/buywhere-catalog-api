import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

const audiences = [
  {
    icon: "🤖",
    title: "AI Agent Developers",
    desc: "Query a structured, normalized product catalog from your agent. One API, one schema, every retailer in Singapore.",
    cta: "Start building",
    ctaHref: "/developers",
  },
  {
    icon: "🏪",
    title: "Merchants & Retailers",
    desc: "Get your catalog discovered by the next wave of AI-powered shopping experiences. No integration work required.",
    cta: "List your catalog",
    ctaHref: "/merchants",
  },
  {
    icon: "🤝",
    title: "Commerce Partners",
    desc: "Collaborate on attribution, referral, and demand routing as AI reshapes how consumers find and buy products.",
    cta: "Explore partnerships",
    ctaHref: "/partners",
  },
];

const features = [
  {
    icon: "⚡",
    title: "Agent-Native API",
    desc: "Designed for LLM agents and AI pipelines. Structured JSON responses, semantic search, and batch queries out of the box.",
  },
  {
    icon: "🗂️",
    title: "Normalized Catalog",
    desc: "Products across retailers unified into a single schema. No more parsing inconsistent HTML or dealing with schema drift.",
  },
  {
    icon: "🌏",
    title: "Southeast Asia First",
    desc: "Deep coverage of Singapore, Malaysia, and Thailand marketplaces — Lazada, Shopee, Qoo10, and more.",
  },
  {
    icon: "🔍",
    title: "Semantic Search",
    desc: "Query products in natural language. 'Waterproof hiking boots under $150' just works.",
  },
  {
    icon: "🔄",
    title: "Real-Time Prices",
    desc: "Live price and availability data refreshed continuously so your agent always quotes accurate information.",
  },
  {
    icon: "🔒",
    title: "Production-Ready",
    desc: "Rate limit controls, audit logs, versioned endpoints, and PDPA-compliant data handling from day one.",
  },
];

const codeSnippet = `import requests

API_KEY = "bw_live_your_key_here"

response = requests.get(
    "https://api.buywhere.ai/v1/search",
    headers={"Authorization": f"Bearer {API_KEY}"},
    params={
        "q": "wireless noise-cancelling headphones",
        "limit": 5
    }
)

products = response.json()["items"]
for p in products:
    print(f"{p['name']} — S$\{p['price']} at {p['source']}")`;

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Nav />

      {/* Hero */}
      <section className="bg-gradient-to-br from-indigo-600 via-indigo-700 to-indigo-900 text-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-24 md:py-32">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 bg-white/10 text-white/90 text-sm font-medium px-3 py-1 rounded-full mb-6">
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              Now in developer beta · Singapore live
            </div>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight mb-6">
              The Product Discovery Infrastructure for AI-Powered Shopping
            </h1>
            <p className="text-xl text-indigo-200 mb-10 leading-relaxed">
              BuyWhere is the neutral catalog layer that AI agents use to find products and route buyers to merchants — starting with Singapore.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/developers"
                className="inline-flex items-center justify-center px-6 py-3 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-colors"
              >
                Get API access →
              </Link>
              <Link
                href="/merchants"
                className="inline-flex items-center justify-center px-6 py-3 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-colors border border-white/20"
              >
                List your catalog
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Who this is for */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Who BuyWhere is for</h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              A two-sided infrastructure layer connecting AI-powered demand with merchant supply.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {audiences.map((a) => (
              <div
                key={a.title}
                className="p-6 rounded-xl border border-gray-100 hover:border-indigo-100 hover:shadow-md transition-all flex flex-col"
              >
                <div className="text-3xl mb-4">{a.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{a.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed flex-1 mb-4">{a.desc}</p>
                <Link
                  href={a.ctaHref}
                  className="text-sm text-indigo-600 font-medium hover:text-indigo-700 transition-colors"
                >
                  {a.cta} →
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">How BuyWhere works</h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              A neutral product-discovery layer connecting merchant catalogs to AI-driven demand.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Merchant catalogs in", desc: "Retailers submit product feeds or we ingest from existing catalog sources." },
              { step: "2", title: "Structured discovery layer", desc: "Products are normalized, deduplicated, and indexed for semantic search." },
              { step: "3", title: "AI agent query & ranking", desc: "Agents search by natural language, filters, or category. Structured JSON back." },
              { step: "4", title: "Routed buyer demand out", desc: "Matched products route demand back to merchants through attribution and referral." },
            ].map((s) => (
              <div key={s.step} className="bg-white rounded-xl p-6 border border-gray-100">
                <div className="w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-sm mb-4">
                  {s.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Code demo */}
      <section className="bg-gray-900 py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row items-start gap-12">
            <div className="flex-1 text-white">
              <h2 className="text-2xl font-bold mb-4">Query Singapore products in 5 lines</h2>
              <p className="text-gray-400 mb-6">
                One API call returns structured product data: name, price, SKU, retailer, image, and availability. No scraping, no parsing.
              </p>
              <Link
                href="/developers"
                className="inline-flex items-center text-indigo-400 font-medium hover:text-indigo-300 transition-colors"
              >
                View full documentation →
              </Link>
            </div>
            <div className="flex-1 w-full">
              <div className="bg-gray-800 rounded-xl overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-700">
                  <div className="w-3 h-3 rounded-full bg-red-500/70"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500/70"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500/70"></div>
                  <span className="ml-2 text-xs text-gray-500 font-mono">search.py</span>
                </div>
                <pre className="p-4 text-sm text-gray-300 font-mono overflow-x-auto leading-relaxed">
                  <code>{codeSnippet}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Built for agent commerce</h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              An infrastructure layer designed from the ground up for AI-native commerce workflows.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="p-6 rounded-xl border border-gray-100 hover:border-indigo-100 hover:shadow-md transition-all"
              >
                <div className="text-3xl mb-4">{f.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why now */}
      <section className="py-20 bg-indigo-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Why AI shopping needs a neutral catalog layer</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Platform APIs surface their own inventory first. Shopee returns Shopee products. Lazada returns Lazada products. For an AI agent trying to find the best match across the market, that is a sales channel — not a catalog.
            </p>
            <p className="text-gray-600 leading-relaxed mb-8">
              BuyWhere has no inventory to sell and no platform to favour. We index products across Singapore&rsquo;s retail landscape into a single, structured API — so AI agents get the market, not one platform&rsquo;s version of it.
            </p>
            <Link
              href="/about"
              className="text-indigo-600 font-medium hover:text-indigo-700 transition-colors"
            >
              Learn more about our approach →
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-white border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { stat: "1M+", label: "Products indexed" },
              { stat: "4+", label: "Retailers connected" },
              { stat: "< 200ms", label: "Median query latency" },
              { stat: "99.9%", label: "API uptime target" },
            ].map((s) => (
              <div key={s.label}>
                <div className="text-3xl font-bold text-indigo-600 mb-1">{s.stat}</div>
                <div className="text-sm text-gray-500">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-indigo-600 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to build agent-native commerce?</h2>
          <p className="text-indigo-200 mb-8 text-lg">
            Whether you&rsquo;re building AI agents, listing your catalog, or exploring commerce partnerships — there&rsquo;s a path for you.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/developers"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-colors text-lg"
            >
              Get API access →
            </Link>
            <Link
              href="/merchants"
              className="inline-flex items-center justify-center px-8 py-4 border border-indigo-400 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors text-lg"
            >
              List your catalog
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
