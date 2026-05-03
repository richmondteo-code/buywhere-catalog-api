import * as jose from "jose";
import fs from "fs";
import path from "path";

const PRIVATE_DIR = path.resolve("private");
const SRC_DIR = path.resolve("src/app/.well-known/agent.json");

async function main() {
  // Read private key
  const privateKeyPem = fs.readFileSync(path.join(PRIVATE_DIR, "agent-key.pem"), "utf-8");
  const privateKey = await jose.importPKCS8(privateKeyPem, "ES256");

  // Build canonical agent card (matching live version)
  const card = {
    name: "Buywhere Product Catalog",
    description: "Cross-border product discovery with intelligent market matching, price comparison, and affiliate attribution across Singapore, China, and global markets.",
    url: "https://buywhere.ai",
    version: "1.0.0",
    capabilities: {
      streaming: true,
      pushNotifications: false,
      stateTransitionHistory: true
    },
    authentication: {
      schemes: ["apiKey", "oauth2"]
    },
    defaultInputModes: ["text"],
    defaultOutputModes: ["text", "json"],
    skills: [
      {
        id: "product-search",
        name: "Product Search",
        description: "Search products by keyword, category, price range, and market",
        tags: ["e-commerce", "search", "products"],
        examples: ["Find Dyson hair dryer under 400 SGD in Singapore", "Organic shampoo in China under 100 CNY"]
      },
      {
        id: "cross-border-match",
        name: "Cross-Border Product Matching",
        description: "Find equivalent products across different markets with price and spec comparison",
        tags: ["cross-border", "matching", "price-comparison", "affiliate"],
        examples: ["What is the China equivalent of this Singapore shampoo?", "Find the cheapest market for iPhone 16 Pro Max"]
      },
      {
        id: "price-history",
        name: "Price History & Alerts",
        description: "Retrieve historical price data and set up price drop alerts",
        tags: ["pricing", "history", "alerts"],
        examples: ["Show me 30-day price history for this product", "Alert me when this drops below 50 SGD"]
      },
      {
        id: "merchant-discovery",
        name: "Merchant & Affiliate Discovery",
        description: "Discover merchants selling a product and retrieve affiliate links",
        tags: ["merchants", "affiliate", "deals"],
        examples: ["Which merchants sell this product in China?", "Get affiliate link for this Singapore merchant"]
      }
    ]
  };

  // Canonical JSON for signing payload
  const canonicalJson = JSON.stringify(card);
  const payload = new TextEncoder().encode(canonicalJson);

  // Sign with JWS compact serialization
  const jws = await new jose.CompactSign(payload)
    .setProtectedHeader({ alg: "ES256", typ: "JWS", kid: "buywhere-agent-card" })
    .sign(privateKey);

  // Card with signature
  const signedCard = { ...card, signature: jws };

  // Write signed card as a TypeScript constant for the route
  const tsContent = `const AGENT_CARD = ${JSON.stringify(signedCard, null, 2)} as const;

export function GET() {
  return Response.json(AGENT_CARD, {
    headers: {
      "Cache-Control": "public, max-age=86400",
    },
  });
}
`;

  // Write JWKS data similarly
  const jwksContent = fs.readFileSync(path.join(PRIVATE_DIR, "agent-jwks.json"), "utf-8");
  const jwksTsContent = `export function GET() {
  return Response.json(${JSON.stringify(JSON.parse(jwksContent))}, {
    headers: {
      "Cache-Control": "public, max-age=86400",
    },
  });
}
`;

  // Write files
  fs.mkdirSync(SRC_DIR, { recursive: true });
  fs.writeFileSync(path.join(SRC_DIR, "route.ts"), tsContent, "utf-8");
  console.log("Wrote src/app/.well-known/agent.json/route.ts");

  const jwksDir = path.resolve("src/app/.well-known/jwks.json");
  fs.mkdirSync(jwksDir, { recursive: true });
  fs.writeFileSync(path.join(jwksDir, "route.ts"), jwksTsContent, "utf-8");
  console.log("Wrote src/app/.well-known/jwks.json/route.ts");

  // Verify the JWS
  const publicJwk = JSON.parse(jwksContent).keys[0];
  const publicKey = await jose.importJWK(publicJwk, "ES256");
  const { payload: decoded } = await jose.jwsVerify(jws, publicKey);
  const decodedStr = new TextDecoder().decode(decoded);
  const verified = decodedStr === canonicalJson;
  console.log("JWS verification:", verified ? "PASSED" : "FAILED");

  if (!verified) {
    console.error("ERROR: JWS verification failed");
    process.exit(1);
  }
  console.log("Done.");
}

main().catch(console.error);
