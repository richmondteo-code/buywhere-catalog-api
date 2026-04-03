import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import Link from "next/link";

const curlExample = `curl -X GET "https://api.buywhere.ai/v1/search" \\
  -H "Authorization: Bearer bw_live_your_key_here" \\
  -G \\
  --data-urlencode "q=wireless headphones" \\
  --data-urlencode "limit=5"`;

const pythonExample = `import requests

client = requests.Session()
client.headers["Authorization"] = "Bearer bw_live_your_key_here"

# Search products
resp = client.get("https://api.buywhere.ai/v1/search", params={
    "q": "wireless headphones",
    "limit": 5,
})
data = resp.json()

for product in data["items"]:
    print(product["name"], product["price"], product["currency"])`;

const langchainExample = `from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
import requests

API_KEY = "bw_live_your_key_here"

@tool
def search_buywhere(query: str) -> str:
    """Search the BuyWhere product catalog for Singapore products."""
    resp = requests.get(
        "https://api.buywhere.ai/v1/search",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"q": query, "limit": 5},
    )
    products = resp.json().get("items", [])
    if not products:
        return "No products found."
    return "\\n".join([f"- {p['name']} | {p['source']} | SGD {p['price']}" for p in products])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = initialize_agent(
    [search_buywhere],
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

result = agent.run("Find the cheapest wireless headphones under $150 in Singapore")
print(result)`;

const crewaiExample = `from crewai import Agent, Task, Crew, Process
from crewai_tools import tool
import requests

API_KEY = "bw_live_your_key_here"

@tool("BuyWhere Product Search")
def search_products(query: str) -> str:
    """Search BuyWhere for products in Singapore."""
    resp = requests.get(
        "https://api.buywhere.ai/v1/search",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"q": query, "limit": 10},
    )
    products = resp.json().get("items", [])
    if not products:
        return "No products found."
    return "\\n".join([f"- {p['name']} | {p['source']} | SGD {p['price']}" for p in products])

researcher = Agent(
    role="Singapore Shopping Researcher",
    goal="Find the best products and prices across Singapore retailers",
    backstory="Expert at Lazada, Shopee, Qoo10, and Singapore e-commerce.",
    tools=[search_products],
    verbose=True,
)
advisor = Agent(
    role="Personal Shopping Advisor",
    goal="Recommend the best options with clear reasoning",
    backstory="Experienced personal shopper who turns data into decisions.",
    verbose=True,
)

crew = Crew(
    agents=[researcher, advisor],
    tasks=[
        Task(
            description="Find wireless headphones under SGD 300 in Singapore",
            expected_output="List of matching products with prices and retailers.",
            agent=researcher,
        ),
        Task(
            description="Recommend the top 3 picks with pros and cons",
            expected_output="Top 3 recommendations with reasoning.",
            agent=advisor,
        ),
    ],
    process=Process.sequential,
)

result = crew.kickoff()
print(result)`;

const tsExample = `const BW_API_KEY = process.env.BUYWHERE_API_KEY ?? "bw_live_your_key_here";
const BASE_URL = "https://api.buywhere.ai/v1";

async function searchProducts(query: string, limit = 5) {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  const res = await fetch(\`\${BASE_URL}/search?\${params}\`, {
    headers: { Authorization: \`Bearer \${BW_API_KEY}\` },
  });
  if (!res.ok) throw new Error(\`BuyWhere API error: \${res.status}\`);
  return res.json() as Promise<{ items: Array<{ name: string; price: number; currency: string }> }>;
}

const { items } = await searchProducts("wireless headphones");
for (const product of items) {
  console.log(product.name, product.price, product.currency);
}`;

const responseExample = `{
  "total": 47,
  "limit": 5,
  "offset": 0,
  "has_more": true,
  "items": [
    {
      "id": 12345,
      "name": "Sony WH-1000XM5 Wireless Headphones",
      "price": 429.00,
      "currency": "SGD",
      "source": "lazada_sg",
      "buy_url": "https://lazada.sg/products/...",
      "affiliate_url": "https://api.buywhere.ai/v1/track/12345",
      "image_url": "https://img.lazcdn.com/...",
      "is_available": true,
      "rating": 4.8,
      "category": "Electronics > Audio > Headphones"
    }
  ]
}`;

const endpoints = [
  {
    method: "GET",
    path: "/v1/search",
    desc: "Full-text product search across Singapore retailers",
    params: ["q", "category", "min_price", "max_price", "platform", "in_stock", "limit", "offset"],
  },
  {
    method: "GET",
    path: "/v1/products/{id}",
    desc: "Get a single product by ID",
    params: ["id (required)"],
  },
  {
    method: "GET",
    path: "/v1/products/best-price",
    desc: "Find the cheapest listing for a product name across all platforms",
    params: ["product_name (required)", "category"],
  },
  {
    method: "GET",
    path: "/v1/deals",
    desc: "Products with significant price drops, sorted by discount percentage",
    params: ["category", "min_discount", "limit"],
  },
  {
    method: "GET",
    path: "/v1/categories",
    desc: "List all supported product categories",
    params: [],
  },
];

export default function DevelopersPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Nav />

      {/* Hero */}
      <section className="bg-gray-900 text-white py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="max-w-2xl">
            <div className="text-indigo-400 text-sm font-mono mb-4">&#47;&#47; developer docs</div>
            <h1 className="text-4xl font-bold mb-4">Build in minutes, not weeks</h1>
            <p className="text-gray-400 text-lg leading-relaxed mb-6">
              The BuyWhere API is REST-based, JSON-native, and designed to integrate into any AI agent framework in minutes.
            </p>
            <div className="flex flex-wrap gap-3">
              <a
                href="https://github.com/richmondteo-code/buywhere-agent-examples"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium rounded-lg border border-gray-700 transition-colors"
              >
                <svg className="w-4 h-4" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
                View examples on GitHub
              </a>
              <a
                href="https://richmondteo-code.github.io/buywhere-catalog-api/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-transparent hover:bg-gray-800 text-gray-300 hover:text-white text-sm font-medium rounded-lg border border-gray-700 transition-colors"
              >
                Full API docs →
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Quickstart */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">
            <span className="text-indigo-600 mr-2">01.</span>Quickstart
          </h2>

          <div className="space-y-8">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">1. Get your API key</h3>
              <p className="text-sm text-gray-500 mb-3">
                <Link href="/api-keys" className="text-indigo-600 hover:underline">Get your API key instantly</Link> — free during beta, no credit card required. You&apos;ll receive a key like <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">bw_beta_xxxx</code> on the next screen.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-700 mb-2">2. Make your first request</h3>
              <p className="text-sm text-gray-500 mb-3">Paste this into your terminal (replace the key):</p>
              <CodeBlock code={curlExample} lang="bash" />
            </div>

            <div>
              <h3 className="font-semibold text-gray-700 mb-2">3. Inspect the response</h3>
              <CodeBlock code={responseExample} lang="json" />
            </div>
          </div>
        </div>
      </section>

      {/* Code examples */}
      <section className="py-16 bg-gray-50 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">
            <span className="text-indigo-600 mr-2">02.</span>Code examples
          </h2>

          <div className="space-y-8">
            <div>
              <h3 className="font-semibold text-gray-700 mb-3">Python</h3>
              <CodeBlock code={pythonExample} lang="python" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-3">LangChain Agent</h3>
              <CodeBlock code={langchainExample} lang="python" />
              <p className="text-xs text-gray-400 mt-2">
                Install: <code className="bg-gray-100 px-1 rounded font-mono">pip install langchain langchain-openai requests</code>
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-3">CrewAI Agent</h3>
              <CodeBlock code={crewaiExample} lang="python" />
              <p className="text-xs text-gray-400 mt-2">
                Install: <code className="bg-gray-100 px-1 rounded font-mono">pip install crewai crewai-tools requests</code>
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-3">TypeScript / Node.js</h3>
              <CodeBlock code={tsExample} lang="typescript" />
              <p className="text-xs text-gray-400 mt-2">
                No dependencies — uses the native <code className="bg-gray-100 px-1 rounded font-mono">fetch</code> API (Node 18+ / all modern runtimes)
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* MCP */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            <span className="text-indigo-600 mr-2">03.</span>MCP Integration
          </h2>
          <p className="text-gray-600 mb-6 leading-relaxed">
            BuyWhere ships a <a href="https://modelcontextprotocol.io" className="text-indigo-600 hover:underline" target="_blank" rel="noopener noreferrer">Model Context Protocol</a> server, so any MCP-compatible AI host (Claude Desktop, Continue, Cursor, custom agents) can search Singapore products without writing any code.
          </p>
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Run the MCP server</h3>
              <p className="text-sm text-gray-500 mb-3">
                The <code className="bg-gray-100 px-1 rounded font-mono text-xs">mcp_server.py</code> file is included with your API key. Install dependencies and run:
              </p>
              <CodeBlock code={`pip install "mcp[cli]" httpx\nBUYWHERE_API_KEY=bw_live_your_key_here python mcp_server.py`} lang="bash" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Claude Desktop config (<code className="bg-gray-100 px-1 rounded text-xs font-mono">claude_desktop_config.json</code>)</h3>
              <CodeBlock code={`{
  "mcpServers": {
    "buywhere": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "BUYWHERE_API_KEY": "bw_live_your_key_here"
      }
    }
  }
}`} lang="json" />
            </div>
            <div className="bg-gray-50 rounded-xl p-5 text-sm text-gray-700">
              <p className="font-semibold mb-2">Available MCP tools</p>
              <ul className="space-y-1 text-gray-600">
                <li><code className="font-mono text-xs bg-white border border-gray-200 px-1.5 py-0.5 rounded mr-2">search_products</code>Keyword search across Lazada, Shopee, Qoo10</li>
                <li><code className="font-mono text-xs bg-white border border-gray-200 px-1.5 py-0.5 rounded mr-2">get_product</code>Full details for a product by ID</li>
                <li><code className="font-mono text-xs bg-white border border-gray-200 px-1.5 py-0.5 rounded mr-2">find_best_price</code>Cheapest listing for a product name across all platforms</li>
                <li><code className="font-mono text-xs bg-white border border-gray-200 px-1.5 py-0.5 rounded mr-2">get_deals</code>Products with significant price drops, sorted by discount</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Auth */}
      <section className="py-16 bg-gray-50 border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            <span className="text-indigo-600 mr-2">04.</span>Authentication
          </h2>
          <p className="text-gray-600 mb-4 leading-relaxed">
            All API requests must include your API key in the <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">Authorization</code> header:
          </p>
          <CodeBlock code={`Authorization: Bearer bw_live_your_key_here`} lang="bash" />
          <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
            <strong>Security:</strong> Never expose your API key in client-side code. Use environment variables and server-side requests only.
          </div>
        </div>
      </section>

      {/* Endpoints */}
      <section className="py-16 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">
            <span className="text-indigo-600 mr-2">05.</span>API Reference
          </h2>
          <div className="space-y-4">
            {endpoints.map((ep) => (
              <div key={ep.path} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-start gap-3 mb-2">
                  <span className="text-xs font-bold font-mono bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                    {ep.method}
                  </span>
                  <code className="text-sm font-mono text-gray-800">{ep.path}</code>
                </div>
                <p className="text-sm text-gray-500 mb-3">{ep.desc}</p>
                <div className="flex flex-wrap gap-2">
                  {ep.params.map((p) => (
                    <span key={p} className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Rate limits */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            <span className="text-indigo-600 mr-2">06.</span>Rate Limits &amp; Errors
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-gray-700 mb-3">Rate limits</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-left text-gray-500">
                    <th className="pb-2">Plan</th>
                    <th className="pb-2">Requests/min</th>
                    <th className="pb-2">Monthly quota</th>
                  </tr>
                </thead>
                <tbody className="text-gray-700">
                  {[
                    ["Free", "10", "1,000"],
                    ["Starter", "60", "100,000"],
                    ["Growth", "300", "1,000,000"],
                    ["Scale", "1,000", "Unlimited"],
                  ].map(([plan, rpm, monthly]) => (
                    <tr key={plan} className="border-b border-gray-50">
                      <td className="py-2">{plan}</td>
                      <td className="py-2">{rpm}</td>
                      <td className="py-2">{monthly}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-3">Error codes</h3>
              <div className="space-y-2 text-sm">
                {[
                  ["401", "Invalid or missing API key"],
                  ["429", "Rate limit exceeded"],
                  ["404", "Product not found"],
                  ["422", "Invalid query parameters"],
                  ["500", "Internal server error"],
                ].map(([code, msg]) => (
                  <div key={code} className="flex gap-3">
                    <span className="font-mono font-bold text-red-500 w-10 shrink-0">{code}</span>
                    <span className="text-gray-600">{msg}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-12 bg-indigo-600 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">Ready to start building?</h2>
          <p className="text-indigo-200 mb-6">Get your API key and make your first query in under 5 minutes.</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link
              href="/api-keys"
              className="inline-flex items-center justify-center px-6 py-3 bg-white text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-colors"
            >
              Get API Key →
            </Link>
            <a
              href="https://github.com/richmondteo-code/buywhere-agent-examples"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-indigo-700 text-white font-semibold rounded-xl hover:bg-indigo-800 border border-indigo-500 transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
              View examples
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  return (
    <div className="bg-gray-900 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-xs text-gray-400 font-mono">{lang}</span>
      </div>
      <pre className="p-4 text-sm text-gray-300 font-mono overflow-x-auto leading-relaxed whitespace-pre">
        <code>{code}</code>
      </pre>
    </div>
  );
}
