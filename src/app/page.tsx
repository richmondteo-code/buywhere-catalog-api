import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

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
    title: "Enterprise-Ready",
    desc: "SLA guarantees, audit logs, rate limit controls, and PDPA-compliant data handling.",
  },
];

const useCases = [
  {
    title: "Shopping Assistants",
    desc: "Let your AI agent find the best deal across dozens of retailers in milliseconds.",
    example: "\"Find me a Sony mirrorless camera under $1,200 with at least 4K video\"",
  },
  {
    title: "Price Comparison Bots",
    desc: "Track price history and alert users when products hit their target price.",
    example: "\"Monitor AirPods Pro and notify me when under $200\"",
  },
  {
    title: "Affiliate Commerce",
    desc: "Power affiliate recommendation engines with accurate, structured product data.",
    example: "\"Recommend running shoes for a marathon training plan\"",
  },
];

const codeSnippet = `import requests

API_KEY = "bw_live_your_key_here"

response = requests.get(
    "https://api.buywhere.ai/v1/products/search",
    headers={"Authorization": f"Bearer {API_KEY}"},
    params={
        "q": "wireless noise-cancelling headphones",
        "country": "SG",
        "limit": 5
    }
)

products = response.json()["products"]
for p in products:
    print(f"{p['name']} — S$\{p['price']} at {p['retailer']}")`;

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
              The Product Catalog API for AI Agent Commerce
            </h1>
            <p className="text-xl text-indigo-200 mb-10 leading-relaxed">
              Query millions of products across Southeast Asia. Structured, normalized, agent-ready.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/developers"
                className="inline-flex items-center justify-center px-6 py-3 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-colors"
              >
                Start building free →
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center justify-center px-6 py-3 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-colors border border-white/20"
              >
                View pricing
              </Link>
            </div>
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
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Everything your agent needs</h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              Built from the ground up for AI-native commerce workflows — not a retrofitted legacy API.
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

      {/* Use cases */}
      <section className="py-20 bg-indigo-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Built for agent commerce use cases</h2>
            <p className="text-lg text-gray-500">Real-world workflows powered by BuyWhere.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {useCases.map((uc) => (
              <div key={uc.title} className="bg-white rounded-xl p-6 shadow-sm border border-indigo-100">
                <h3 className="font-semibold text-gray-900 mb-2">{uc.title}</h3>
                <p className="text-sm text-gray-500 mb-4 leading-relaxed">{uc.desc}</p>
                <div className="bg-indigo-50 rounded-lg p-3 text-sm text-indigo-700 italic">
                  {uc.example}
                </div>
              </div>
            ))}
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
              { stat: "99.9%", label: "API uptime SLA" },
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
            Get your API key in minutes. First 1,000 queries free, no credit card required.
          </p>
          <Link
            href="/contact"
            className="inline-flex items-center justify-center px-8 py-4 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-colors text-lg"
          >
            Get your API key →
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
