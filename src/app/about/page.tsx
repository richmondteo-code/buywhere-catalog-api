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

const team = [
  {
    name: "Singapore HQ",
    detail: "We're headquartered in Singapore, embedded in the SEA e-commerce ecosystem.",
  },
  {
    name: "Remote-first",
    detail: "Our team spans Singapore, Indonesia, and Malaysia — building for the region, from the region.",
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
            <h1 className="text-4xl font-bold mb-4">We&apos;re building the infrastructure for AI-native commerce</h1>
            <p className="text-indigo-200 text-lg leading-relaxed">
              BuyWhere exists because every AI shopping agent deserves reliable, structured product data — not scraped HTML and guesswork.
            </p>
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Our mission</h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                Build the definitive agent-native product catalog API for AI agent commerce, starting with Singapore.
              </p>
              <p className="text-gray-600 leading-relaxed mb-4">
                E-commerce in Southeast Asia is fragmented across dozens of marketplaces, each with its own schema, authentication model, and data quality standard. AI agents trying to help users shop are stuck scraping, guessing, and failing.
              </p>
              <p className="text-gray-600 leading-relaxed">
                BuyWhere normalizes all of that into a single, clean, agent-ready API. Query once, get structured results from Lazada, Shopee, Qoo10, and more — all in a consistent format your agent can act on immediately.
              </p>
            </div>
            <div className="bg-indigo-50 rounded-2xl p-8">
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

      {/* Values */}
      <section className="py-16 bg-gray-50 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-10 text-center">What we believe</h2>
          <div className="grid sm:grid-cols-2 gap-6">
            {values.map((v) => (
              <div key={v.title} className="bg-white rounded-xl p-6 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-2">{v.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Singapore focus */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl mx-auto text-center">
            <div className="text-5xl mb-4">🇸🇬</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Why Singapore first?</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Singapore is one of the most digitally advanced retail markets in Southeast Asia — high internet penetration, strong logistics infrastructure, and a tech-forward consumer base. It&apos;s the ideal launchpad for agent-native commerce.
            </p>
            <p className="text-gray-600 leading-relaxed">
              Once we&apos;ve proven the model in Singapore, we expand across the region — Malaysia, Thailand, Indonesia, and beyond.
            </p>
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-10 text-center">Our team</h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
            {team.map((t) => (
              <div key={t.name} className="bg-white rounded-xl p-6 border border-gray-100 text-center">
                <h3 className="font-semibold text-gray-900 mb-2">{t.name}</h3>
                <p className="text-sm text-gray-500">{t.detail}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-10">
            <p className="text-gray-500 mb-4">We&apos;re hiring engineers, data specialists, and developer advocates.</p>
            <Link
              href="/contact"
              className="inline-flex items-center justify-center px-5 py-2.5 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors text-sm"
            >
              Get in touch →
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
