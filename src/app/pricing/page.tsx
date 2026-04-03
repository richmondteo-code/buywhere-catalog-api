import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import Link from "next/link";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    desc: "Try BuyWhere with no commitment.",
    queries: "1,000 queries/mo",
    rateLimit: "10 req/min",
    support: "Community",
    features: [
      "Product search API",
      "Singapore catalog",
      "JSON responses",
      "Community support",
    ],
    cta: "Get started",
    ctaHref: "/contact",
    highlight: false,
  },
  {
    name: "Starter",
    price: "$99",
    period: "/month",
    desc: "For indie developers and small projects.",
    queries: "100,000 queries/mo",
    rateLimit: "60 req/min",
    support: "Email",
    features: [
      "Everything in Free",
      "100K queries/month",
      "Price history data",
      "Batch API access",
      "Email support",
      "99.5% uptime SLA",
    ],
    cta: "Start building",
    ctaHref: "/contact",
    highlight: false,
  },
  {
    name: "Growth",
    price: "$499",
    period: "/month",
    desc: "For teams building production AI agents.",
    queries: "1,000,000 queries/mo",
    rateLimit: "300 req/min",
    support: "Priority",
    features: [
      "Everything in Starter",
      "1M queries/month",
      "Semantic search",
      "Multi-country (SG, MY, TH)",
      "Webhook notifications",
      "Priority support",
      "99.9% uptime SLA",
    ],
    cta: "Get Growth",
    ctaHref: "/contact",
    highlight: true,
  },
  {
    name: "Scale",
    price: "$1,999",
    period: "/month",
    desc: "For high-volume production workloads.",
    queries: "Unlimited queries",
    rateLimit: "1,000 req/min",
    support: "Dedicated",
    features: [
      "Everything in Growth",
      "Unlimited queries",
      "Custom rate limits",
      "Dedicated infrastructure",
      "Custom data integrations",
      "Dedicated support",
      "99.99% uptime SLA",
      "PDPA compliance docs",
    ],
    cta: "Talk to us",
    ctaHref: "/contact",
    highlight: false,
  },
];

const faqs = [
  {
    q: "What counts as a query?",
    a: "Each API request to /v1/products/search or /v1/products/{id} counts as one query. Batch requests count as one query per product returned.",
  },
  {
    q: "Can I switch plans mid-month?",
    a: "Yes. Upgrades take effect immediately (prorated). Downgrades take effect at the next billing cycle.",
  },
  {
    q: "Do unused queries roll over?",
    a: "No. Quota resets on your monthly billing date.",
  },
  {
    q: "Is there a free trial for paid plans?",
    a: "Contact us — we offer 14-day trials for Growth and Scale on request.",
  },
  {
    q: "What payment methods do you accept?",
    a: "Visa, Mastercard, and bank transfer (for annual Scale plans).",
  },
  {
    q: "What happens if I exceed my quota?",
    a: "Requests return 429 errors until your next billing cycle. You can upgrade anytime to avoid interruption.",
  },
];

export default function PricingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Nav />

      {/* Header */}
      <section className="bg-white py-16 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Simple, predictable pricing</h1>
          <p className="text-lg text-gray-500 max-w-xl mx-auto">
            Start free. Scale as your agent grows. No hidden fees, no per-product charges.
          </p>
        </div>
      </section>

      {/* Plans */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
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
                  <div className="text-gray-400 text-xs">{plan.rateLimit} · {plan.support} support</div>
                </div>

                <ul className="space-y-2 text-sm text-gray-600 flex-1 mb-6">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" viewBox="0 0 16 16" fill="none">
                        <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
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

      {/* Enterprise */}
      <section className="py-12 bg-white border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 bg-indigo-50 rounded-2xl p-8">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">Enterprise</h3>
              <p className="text-gray-600">
                Custom volume pricing, dedicated SLAs, private deployments, and integration support for large-scale deployments.
              </p>
            </div>
            <Link
              href="/contact"
              className="shrink-0 px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Contact sales →
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-10 text-center">Frequently asked questions</h2>
          <div className="space-y-6">
            {faqs.map((faq) => (
              <div key={faq.q} className="bg-white rounded-xl border border-gray-100 p-5">
                <h3 className="font-semibold text-gray-900 mb-2">{faq.q}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
