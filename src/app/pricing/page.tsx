import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import Link from "next/link";

const plans = [
  {
    name: "Starter",
    price: "$299",
    period: "/month",
    desc: "For indie developers and early-stage AI projects exploring commerce-aware features for the first time.",
    queries: "30,000 queries/mo",
    overage: "$0.015/query",
    rateLimit: "10 req/sec",
    dataFreshness: "Daily",
    sla: "99.5%",
    support: "Community + docs",
    seats: "1 seat",
    features: [
      "Full Singapore catalog",
      "Structured product schema",
      "Semantic search",
      "Price comparison across merchants",
      "Annual billing: 2 months free",
    ],
    cta: "Start building",
    ctaHref: "/docs",
    highlight: false,
  },
  {
    name: "Growth",
    price: "$999",
    period: "/month",
    desc: "For growing teams shipping production AI agents that need reliable product data at scale.",
    queries: "150,000 queries/mo",
    overage: "$0.010/query",
    rateLimit: "50 req/sec",
    dataFreshness: "Hourly",
    sla: "99.9%",
    support: "Email (48h response)",
    seats: "Up to 5 seats",
    features: [
      "Everything in Starter",
      "Hourly data freshness",
      "99.9% uptime SLA",
      "Up to 5 team seats",
      "Annual billing: 2 months free",
    ],
    cta: "Get started",
    ctaHref: "/docs",
    highlight: true,
  },
  {
    name: "Scale",
    price: "$2,999",
    period: "/month",
    desc: "For high-volume AI platforms where data freshness, uptime guarantees, and enterprise support are business-critical.",
    queries: "600,000 queries/mo",
    overage: "$0.008/query",
    rateLimit: "200 req/sec",
    dataFreshness: "Real-time (15-min)",
    sla: "99.95% + credits",
    support: "Priority email (4h response)",
    seats: "Up to 20 seats",
    features: [
      "Everything in Growth",
      "Real-time data (15-min refresh)",
      "Webhooks (catalog change alerts)",
      "99.95% SLA + service credits",
      "Up to 20 team seats",
      "Annual billing: 2 months free",
    ],
    cta: "Talk to us",
    ctaHref: "/contact",
    highlight: false,
  },
];

const comparisonFeatures = [
  { feature: "Monthly API queries", starter: "30,000", growth: "150,000", scale: "600,000", enterprise: "Custom" },
  { feature: "Overage rate", starter: "$0.015/query", growth: "$0.010/query", scale: "$0.008/query", enterprise: "Negotiated" },
  { feature: "Products indexed", starter: "Full SG catalog", growth: "Full SG catalog", scale: "Full SG catalog", enterprise: "Custom catalogs" },
  { feature: "Data freshness", starter: "Daily", growth: "Hourly", scale: "Real-time (15-min)", enterprise: "Real-time + webhooks" },
  { feature: "Uptime SLA", starter: "99.5%", growth: "99.9%", scale: "99.95% + credits", enterprise: "Custom SLA" },
  { feature: "API rate limit", starter: "10 req/sec", growth: "50 req/sec", scale: "200 req/sec", enterprise: "Custom" },
  { feature: "Support", starter: "Community + docs", growth: "Email (48h)", scale: "Priority email (4h)", enterprise: "Dedicated account manager" },
  { feature: "Structured product schema", starter: "✓", growth: "✓", scale: "✓", enterprise: "✓" },
  { feature: "Semantic search", starter: "✓", growth: "✓", scale: "✓", enterprise: "✓" },
  { feature: "Price comparison across merchants", starter: "✓", growth: "✓", scale: "✓", enterprise: "✓" },
  { feature: "Webhooks (catalog change alerts)", starter: "—", growth: "—", scale: "✓", enterprise: "✓" },
  { feature: "SSO / team seats", starter: "1 seat", growth: "Up to 5 seats", scale: "Up to 20 seats", enterprise: "Unlimited" },
  { feature: "Custom data integrations", starter: "—", growth: "—", scale: "—", enterprise: "✓" },
  { feature: "Annual billing discount", starter: "2 months free", growth: "2 months free", scale: "2 months free", enterprise: "Negotiated" },
];

const faqs = [
  {
    q: "Can I upgrade or downgrade my plan at any time?",
    a: "Yes. Plan changes take effect at the start of your next billing cycle. If you upgrade mid-cycle, we prorate the difference. If you downgrade, your current tier remains active until the cycle ends.",
  },
  {
    q: "What exactly counts as an API query?",
    a: "A query is any single authenticated request to a BuyWhere API endpoint — whether it's a product search, a price lookup, or a catalog fetch. Batch requests that return multiple results still count as one query. Requests that return errors (4xx/5xx) are not counted.",
  },
  {
    q: "Is there a free trial or sandbox environment?",
    a: "Yes. All plans include a 14-day free trial with 5,000 sandbox queries against a representative subset of the catalog. No credit card required to start. Production access begins when you upgrade.",
  },
  {
    q: "Do you offer annual billing discounts?",
    a: "Yes — pay annually and get two months free (equivalent to ~17% off). Annual plans are available on all tiers including Enterprise. Contact us to arrange invoiced annual billing.",
  },
  {
    q: "What is the Merchant SaaS add-on?",
    a: "The Merchant SaaS add-on is designed for Singapore retailers who want to expose their own inventory through the BuyWhere API ecosystem — powering AI agents, comparison tools, or storefronts built by BuyWhere developer partners. It includes a merchant dashboard, catalog management tools, and query analytics. The $500/month base covers up to 10,000 queries against your merchant data; additional queries are billed at $0.05 each.",
  },
];

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" viewBox="0 0 16 16" fill="none">
      <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function PricingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Nav />

      {/* Header */}
      <section className="bg-white py-16 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            The product catalog API your AI agents can trust.
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            BuyWhere gives your AI agent instant access to structured, real-time product data from Singapore&apos;s top merchants — so it can find, compare, and act on real products without the scraping.
          </p>
        </div>
      </section>

      {/* Plans */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative bg-white rounded-2xl border p-6 flex flex-col ${
                  plan.highlight
                    ? "border-indigo-500 shadow-lg shadow-indigo-100"
                    : "border-gray-200"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                      Most popular
                    </span>
                  </div>
                )}

                <div className="mb-4">
                  <h3 className="font-bold text-gray-900 text-lg mb-1">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-500 text-sm">{plan.period}</span>
                  </div>
                  <p className="text-sm text-gray-500">{plan.desc}</p>
                </div>

                <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm">
                  <div className="text-gray-700 font-medium">{plan.queries}</div>
                  <div className="text-gray-400 text-xs">
                    {plan.overage} overage · {plan.rateLimit} · {plan.sla} SLA
                  </div>
                </div>

                <ul className="space-y-2 text-sm text-gray-600 flex-1 mb-6">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <CheckIcon />
                      {f}
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.ctaHref}
                  className={`w-full text-center py-2.5 rounded-xl font-semibold text-sm transition-colors ${
                    plan.highlight
                      ? "bg-indigo-600 text-white hover:bg-indigo-700"
                      : "bg-gray-100 text-gray-800 hover:bg-gray-200"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Enterprise + Merchant SaaS */}
      <section className="py-12 bg-white border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-4">
          {/* Enterprise */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 bg-indigo-50 rounded-2xl p-8">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">Enterprise — Custom pricing</h3>
              <p className="text-gray-600">
                For large organizations with custom data requirements, compliance mandates, white-label needs, or regional expansion plans. Unlimited seats, dedicated SLA, custom data integrations.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 shrink-0">
              <Link
                href="/contact"
                className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors text-center"
              >
                Contact sales
              </Link>
              <Link
                href="/contact"
                className="px-6 py-3 bg-white text-indigo-600 font-semibold rounded-xl border border-indigo-200 hover:bg-indigo-50 transition-colors text-center"
              >
                Schedule a call
              </Link>
            </div>
          </div>

          {/* Merchant SaaS */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 bg-gray-50 rounded-2xl p-8 border border-gray-200">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">Merchant SaaS Add-on — $500/month + $0.05/query</h3>
              <p className="text-gray-600">
                For Singapore merchants who want to power their own AI-native storefronts, chatbots, or recommendation engines using the BuyWhere catalog API. Includes merchant dashboard, catalog management, and query analytics.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 shrink-0">
              <Link
                href="/contact"
                className="px-6 py-3 bg-gray-800 text-white font-semibold rounded-xl hover:bg-gray-900 transition-colors text-center"
              >
                Add to your plan
              </Link>
              <Link
                href="/docs"
                className="px-6 py-3 bg-white text-gray-700 font-semibold rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors text-center"
              >
                Learn more
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Feature comparison table */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">Compare plans</h2>
          <div className="overflow-x-auto rounded-2xl border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-6 py-4 font-semibold text-gray-700 w-1/3">Feature</th>
                  <th className="px-4 py-4 font-semibold text-gray-700 text-center">Starter</th>
                  <th className="px-4 py-4 font-semibold text-indigo-700 text-center bg-indigo-50">Growth</th>
                  <th className="px-4 py-4 font-semibold text-gray-700 text-center">Scale</th>
                  <th className="px-4 py-4 font-semibold text-gray-700 text-center">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {comparisonFeatures.map((row, i) => (
                  <tr key={row.feature} className={i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                    <td className="px-6 py-3 text-gray-700 font-medium">{row.feature}</td>
                    <td className="px-4 py-3 text-gray-500 text-center">{row.starter}</td>
                    <td className="px-4 py-3 text-gray-700 text-center bg-indigo-50/50 font-medium">{row.growth}</td>
                    <td className="px-4 py-3 text-gray-500 text-center">{row.scale}</td>
                    <td className="px-4 py-3 text-gray-500 text-center">{row.enterprise}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ */}
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

      {/* Bottom CTA */}
      <section className="py-16 bg-gradient-to-br from-indigo-600 to-indigo-800 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to start building?</h2>
          <p className="text-indigo-200 mb-8">
            14-day free trial. 5,000 sandbox queries. No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/docs"
              className="px-8 py-3 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-colors"
            >
              View docs
            </Link>
            <Link
              href="/contact"
              className="px-8 py-3 border border-indigo-400 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Talk to sales
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
