import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing — BuyWhere Product Catalog API & MCP Server | Singapore",
  description:
    "BuyWhere pricing: pay per product search query or subscribe for higher limits. AI agent-ready product catalog API with live prices from Shopee, Lazada, and 20+ Singapore retailers. Free tier available.",
};

const betaFeatures = [
  "Full Singapore product catalog",
  "Structured product schema (JSON)",
  "Semantic natural-language search",
  "Price comparison across merchants",
  "Real-time availability data",
  "Rate-limited API access",
];

const perQueryPricing = [
  {
    endpoint: "/v1/products/search",
    description: "Natural language & semantic product search",
    price: "S$0.002",
    note: "per search call",
  },
  {
    endpoint: "/v1/products/{id}",
    description: "Structured product lookup by ID",
    price: "S$0.005",
    note: "per lookup call",
  },
  {
    endpoint: "/v1/products/{id}/links",
    description: "Affiliate link generation for product",
    price: "S$0.05",
    note: "per affiliate-link call",
  },
];

const subscriptionTiers = [
  {
    name: "Free",
    price: "S$0",
    description: "For experimentation and testing",
    limit: "100 calls/day",
  },
  {
    name: "Pro",
    price: "USD $29/mo",
    description: "For production pilots",
    limit: "50,000 calls/day",
  },
  {
    name: "Scale",
    price: "USD $99/mo",
    description: "For live agent workloads",
    limit: "200,000 calls/day",
  },
];

const volumeTier = {
  name: "Volume",
  price: "S$299/mo",
  description: "Unlimited calls capped at 1M/month",
  features: [
    "100,000 search calls included",
    "50,000 lookup calls included",
    "5,000 affiliate-link calls included",
    "Overage at reduced per-call rates",
  ],
};

const modelComparison = [
  {
    aspect: "Best for",
    subscription: "Predictable, committed usage",
    perQuery: "Variable, experimental volume",
  },
  {
    aspect: "Cost model",
    subscription: "Fixed monthly fee",
    perQuery: "Pay per call",
  },
  {
    aspect: "Free tier",
    subscription: "100 calls/day hard cap",
    perQuery: "1,000 search + 500 lookup + 100 affiliate/mo",
  },
  {
    aspect: "Affiliate-link model",
    subscription: "Uses daily quota",
    perQuery: "S$0.05/call — offset by earned commission",
  },
];

const faqs = [
  {
    q: "Is BuyWhere free during the beta?",
    a: "Yes. During developer beta, API access is free with rate limits. We want developers building on BuyWhere before we finalize pricing. When we introduce paid tiers, existing beta users will get advance notice and transition support.",
  },
  {
    q: "What exactly counts as an API query?",
    a: "A query is any single authenticated request to a BuyWhere API endpoint — whether it's a product search, a price lookup, or a catalog fetch. Batch requests that return multiple results still count as one query. Requests that return errors (4xx/5xx) are not counted.",
  },
  {
    q: "How does the free tier work?",
    a: "The free tier has a hard daily cap of 100 calls per day for search and lookup endpoints, plus 100 affiliate-link calls per month. There is no rollover — unused quota does not carry over to the next day. Once you hit the cap, you must wait for the daily reset or upgrade to a paid plan.",
  },
  {
    q: "What's the difference between subscription and per-query pricing?",
    a: "Subscription (daily rate limit) is best for predictable, committed usage — you pay a fixed monthly fee and get a daily quota of calls. Per-query is best for variable, experimental volume — you pay only for the calls you actually make. Per-query pricing is pay-as-you-go with no monthly commitment. Both models can coexist on your account.",
  },
  {
    q: "How does BuyWhere make money?",
    a: "BuyWhere's business model is built around referral fees, merchant partnerships, and demand routing economics. When AI agents use our catalog to match buyers with products, we participate in the commerce economics of that transaction. We are not a subscription API business — we succeed when merchants get qualified demand.",
  },
  {
    q: "How does the affiliate-link pricing work?",
    a: "Affiliate-link calls cost S$0.05 per call. However, when your AI agent converts a product lookup into a purchase, you earn a referral commission that offsets this cost. For active affiliate agents, the effective net cost of the affiliate-link endpoint approaches zero.",
  },
  {
    q: "Will there be paid tiers later?",
    a: "We offer both subscription (daily rate limit) and per-query (per-call) pricing now. Subscription plans start at USD $29/month for 50,000 calls/day. Per-query pricing starts at S$0.002 per search call. High-volume developers can also opt for the Volume tier at S$299/month for 1M calls/month.",
  },
  {
    q: "I'm a merchant. Is there a cost to list my catalog?",
    a: "No. During beta, merchant catalog ingestion is free. Our long-term model is built around demand routing and referral economics, not listing fees. Get in touch via the Merchants page to start the conversation.",
  },
];

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" viewBox="0 0 16 16" fill="none">
      <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" viewBox="0 0 16 16" fill="none">
      <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function PricingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Nav />

      <section className="bg-white py-16 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 text-sm font-medium px-3 py-1 rounded-full mb-6">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Developer Beta — Open Access
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Two ways to pay for BuyWhere API access
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Subscribe for predictable daily quota — or pay per query for flexible, variable usage.
            Both models grow with you.
          </p>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid md:grid-cols-2 gap-12">
            <div className="bg-gray-50 rounded-2xl border border-gray-200 p-8">
              <div className="flex items-center gap-2 mb-6">
                <span className="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-sm font-medium text-indigo-700">
                  Per-Query
                </span>
                <span className="text-sm text-gray-500">Pay as you grow</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-6">Endpoint pricing</h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 font-semibold text-gray-900">Endpoint</th>
                    <th className="text-right py-3 font-semibold text-gray-900">Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {perQueryPricing.map((p) => (
                    <tr key={p.endpoint}>
                      <td className="py-4">
                        <div className="font-mono text-xs text-gray-600 mb-1">{p.endpoint}</div>
                        <div className="text-gray-700">{p.description}</div>
                        <div className="text-xs text-gray-400 mt-1">{p.note}</div>
                      </td>
                      <td className="py-4 text-right">
                        <span className="font-bold text-gray-900">{p.price}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="mt-6 rounded-xl bg-emerald-50 border border-emerald-100 p-4">
                <div className="flex items-start gap-2">
                  <PlusIcon />
                  <div>
                    <p className="text-sm font-semibold text-emerald-900">Volume tier available</p>
                    <p className="text-sm text-emerald-700 mt-1">
                      {volumeTier.price} — {volumeTier.description}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-2xl border border-gray-200 p-8">
              <div className="flex items-center gap-2 mb-6">
                <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
                  Subscription
                </span>
                <span className="text-sm text-gray-500">Predictable daily quota</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-6">Daily rate limit tiers</h2>
              <div className="space-y-4">
                {subscriptionTiers.map((tier) => (
                  <div key={tier.name} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                    <div>
                      <div className="font-semibold text-gray-900">{tier.name}</div>
                      <div className="text-sm text-gray-500">{tier.description}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900">{tier.price}</div>
                      <div className="text-xs text-gray-400">{tier.limit}</div>
                    </div>
                  </div>
                ))}
              </div>
              <Link
                href="/api-keys"
                className="mt-6 block w-full text-center py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-colors"
              >
                Get your API key →
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 bg-indigo-50 border-y border-indigo-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Which model is right for you?</h2>
          </div>
          <div className="overflow-hidden rounded-2xl border border-indigo-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="py-4 pl-6 pr-4 text-left font-semibold text-gray-900">Aspect</th>
                  <th className="px-4 py-4 text-center font-semibold text-indigo-700">Per-Query</th>
                  <th className="px-4 py-4 text-center font-semibold text-emerald-700">Subscription</th>
                </tr>
              </thead>
              <tbody>
                {modelComparison.map((row, i) => (
                  <tr key={row.aspect} className={i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                    <td className="py-3.5 pl-6 pr-4 font-medium text-gray-700">{row.aspect}</td>
                    <td className="px-4 py-3.5 text-center text-gray-600">{row.perQuery}</td>
                    <td className="px-4 py-3.5 text-center text-gray-600">{row.subscription}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="py-16 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="bg-white rounded-2xl border border-indigo-200 shadow-lg shadow-indigo-50 p-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="font-bold text-gray-900 text-xl">Developer Beta</h3>
                <p className="text-gray-500 text-sm">Full catalog access with rate limits</p>
              </div>
              <div className="text-right">
                <span className="text-3xl font-bold text-gray-900">Free</span>
                <p className="text-gray-400 text-xs">during beta</p>
              </div>
            </div>

            <ul className="space-y-3 text-sm text-gray-600 mb-8">
              {betaFeatures.map((f) => (
                <li key={f} className="flex items-start gap-2">
                  <CheckIcon />
                  {f}
                </li>
              ))}
            </ul>

            <div className="rounded-xl bg-amber-50 border border-amber-100 p-4 mb-6">
              <p className="text-sm text-amber-800">
                <strong>Free tier hard cap:</strong> 100 calls/day — unused quota does not roll over.
                No credit card required. Upgrade anytime.
              </p>
            </div>

            <Link
              href="/api-keys"
              className="block w-full text-center py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-colors"
            >
              Get your API key →
            </Link>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">For developers</h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                BuyWhere offers two pricing models to fit different developer cost psychology.
                Per-query pricing is ideal for experimental and variable workloads — pay only for
                what you use. Subscription plans offer predictable monthly costs for committed usage.
              </p>
              <p className="text-gray-500 text-sm">
                Both models include access to the full Singapore product catalog and all BuyWhere API endpoints.
              </p>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">For merchants</h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                Catalog listing is free during beta. Our long-term merchant model is built around
                referral economics and demand routing — not listing fees or SaaS subscriptions.
                We make money when AI agents route qualified buyers to your store.
              </p>
              <p className="text-gray-500 text-sm">
                <Link href="/merchants" className="text-indigo-600 hover:text-indigo-700">
                  Learn more about merchant participation →
                </Link>
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 bg-indigo-50 rounded-2xl p-8">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">Need higher rate limits or custom data?</h3>
              <p className="text-gray-600">
                For teams with production-scale requirements, custom catalog needs, or partnership opportunities — let&rsquo;s talk.
              </p>
            </div>
            <Link
              href="/contact"
              className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors text-center shrink-0"
            >
              Contact us
            </Link>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-10 text-center">Frequently asked questions</h2>
          <div className="space-y-6">
            {faqs.map((faq) => (
              <div key={faq.q} className="bg-gray-50 rounded-xl border border-gray-100 p-5">
                <h3 className="font-semibold text-gray-900 mb-2">{faq.q}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-gradient-to-br from-indigo-600 to-indigo-800 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to start building?</h2>
          <p className="text-indigo-200 mb-8">
            Get your API key and make your first query in under 5 minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/api-keys"
              className="px-8 py-3 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-colors"
            >
              Get API key →
            </Link>
            <Link
              href="/quickstart"
              className="px-8 py-3 border border-indigo-400 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              View quickstart
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
