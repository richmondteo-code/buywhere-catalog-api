import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import Link from "next/link";

const values = [
  {
    title: "Agent-first design",
    desc: "We build for AI agents as the primary consumer. Every API decision optimizes for programmatic access, structured output, and batch efficiency.",
  },
  {
    title: "Southeast Asia focus",
    desc: "We're not trying to boil the ocean. Singapore first, done properly — then expand. Deep coverage beats shallow global coverage every time.",
  },
  {
    title: "Developer respect",
    desc: "Clear docs, honest pricing, no dark patterns. We succeed when developers succeed, so we make integration as frictionless as possible.",
  },
  {
    title: "Data quality over quantity",
    desc: "A million normalized, accurate products beats 10 million scraped ones. We invest heavily in data cleaning and schema normalization.",
  },
];

export default function AboutPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Nav />

      {/* Hero */}
      <section className="bg-indigo-600 text-white py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-bold mb-4">Why BuyWhere</h1>
            <p className="text-indigo-200 text-lg leading-relaxed">
              AI agents can reason about what to buy. They struggle to know what exists, what it costs, or where to find it.
            </p>
          </div>
        </div>
      </section>

      {/* The Problem */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">The Problem</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Every retailer in Singapore has its own API, its own schema, and its own access requirements — if it has a public API at all. The major platforms (Shopee, Lazada) do have APIs, but those APIs surface their own inventory first. A Lazada API call returns Lazada products. A Shopee API call returns Shopee products. For an AI agent trying to find the best match for a user across the market, that is not a catalog — it is a sales channel.
            </p>
            <p className="text-gray-600 leading-relaxed">
              For developers, that means writing and maintaining integrations for every retailer you want to cover, reconciling incompatible schemas, handling auth rotation, and absorbing breakage when retailers change their APIs. Most teams do not do this. They narrow scope, limit coverage, or build on top of search results and hope the data is good enough.
            </p>
          </div>
        </div>
      </section>

      {/* The Solution */}
      <section className="py-16 bg-gray-50 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">The Solution</h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                BuyWhere is a single, neutral product catalog API for Singapore commerce.
              </p>
              <p className="text-gray-600 leading-relaxed mb-4">
                One API key. One schema. Products from across the market, not just from one platform. Structured metadata — title, price, availability, specs, category, affiliate link — returned in a consistent format that your agent can reason against without preprocessing.
              </p>
              <p className="text-gray-600 leading-relaxed">
                Every response includes an affiliate-linked purchase URL. When a user clicks through and buys, you earn commission. The catalog is free to query; monetisation comes from the purchase path.
              </p>
            </div>
            <div className="bg-white rounded-2xl p-8 border border-gray-100">
              <div className="text-5xl font-bold text-indigo-600 mb-2">Day 90</div>
              <div className="text-gray-700 font-semibold mb-4">Target milestone</div>
              <ul className="space-y-3 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>
                  1,000,000 products indexed across Singapore
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>
                  1,000,000 API queries/month
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>
                  $50,000/month in affiliate commission revenue
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Why Neutral Matters */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Why Neutral Matters</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Shopee and Lazada are incentivised to surface their own sellers. That is rational for them. It is a problem for you if you are trying to build a product that answers &ldquo;what is the best option across the market?&rdquo;
            </p>
            <p className="text-gray-600 leading-relaxed">
              BuyWhere has no inventory to sell and no platform to favour. We index products from independent Singapore merchants and consumer electronics retailers alongside the major platforms. When your agent calls BuyWhere, it gets the market — not a platform&rsquo;s interpretation of it.
            </p>
          </div>
        </div>
      </section>

      {/* Who It Is For */}
      <section className="py-16 bg-gray-50 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">Who It&apos;s For</h2>
          <p className="text-gray-600 leading-relaxed mb-8 max-w-3xl">
            BuyWhere is for developers building AI applications where a user might end up buying something. If you need product data that your agent can use without transformation, and you want that data to cover Singapore&rsquo;s retail market rather than one walled garden, BuyWhere is the shortest path.
          </p>
          <div className="grid sm:grid-cols-2 gap-4 max-w-3xl">
            {[
              { label: "AI shopping assistants", desc: "LLM-powered agents that handle product discovery in response to natural language" },
              { label: "Price comparison tools", desc: "Structured catalog data across merchants, consistent schema, no scraping" },
              { label: "Gift and recommendation engines", desc: "Attribute-rich product data to match context and intent" },
              { label: "Commerce-integrated agents", desc: "Any AI application where a user might end up buying something" },
            ].map((item) => (
              <div key={item.label} className="bg-white rounded-xl p-5 border border-gray-100">
                <div className="font-semibold text-gray-900 text-sm mb-1">{item.label}</div>
                <div className="text-gray-500 text-sm leading-relaxed">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-10 text-center">What we believe</h2>
          <div className="grid sm:grid-cols-2 gap-6">
            {values.map((v) => (
              <div key={v.title} className="bg-gray-50 rounded-xl p-6 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-2">{v.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About BuyWhere */}
      <section className="py-16 bg-gray-50 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">About BuyWhere</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              BuyWhere is an early-stage API company building the infrastructure layer for AI agent commerce in Singapore. We are indexing Singapore&rsquo;s retail market — starting with consumer electronics, home goods, and lifestyle products — with a goal of one million indexed products. The API is in active development and open for developer beta access.
            </p>
            <p className="text-gray-600 leading-relaxed mb-4">
              We are headquartered in Singapore, embedded in the SEA e-commerce ecosystem. Our team spans Singapore, Indonesia, and Malaysia — building for the region, from the region.
            </p>
            <p className="text-gray-500 text-sm leading-relaxed">
              We are not affiliated with Shopee, Lazada, or any individual retailer. Our business model is affiliate commission on purchases originated through the API, not platform lock-in.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <p className="text-gray-500 mb-4">We&rsquo;re hiring engineers, data specialists, and developer advocates.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/developers"
              className="inline-flex items-center justify-center px-5 py-2.5 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors text-sm"
            >
              Get API access →
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center justify-center px-5 py-2.5 border border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-colors text-sm"
            >
              Get in touch
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
