import * as jose from "jose";
import fs from "fs";
import path from "path";

async function main() {
  const jwksContent = fs.readFileSync(path.resolve("private/agent-jwks.json"), "utf-8");
  const jwks = JSON.parse(jwksContent);
  const publicKey = await jose.importJWK(jwks.keys[0], "ES256");

  const routeContent = fs.readFileSync(path.resolve("src/app/.well-known/agent.json/route.ts"), "utf-8");
  const cardMatch = routeContent.match(/const AGENT_CARD = ({[\s\S]*?}) as const/);
  if (!cardMatch) { console.error("Could not extract card"); process.exit(1); }
  
  const card = eval(`(${cardMatch[1]})`);
  const signature = card.signature;
  
  const { payload } = await jose.compactVerify(signature, publicKey);
  const expectedCard = { ...card };
  delete expectedCard.signature;
  const expectedPayload = new TextDecoder().decode(payload);
  const expectedCanonical = JSON.stringify(expectedCard);
  
  if (expectedPayload === expectedCanonical) {
    console.log("JWS VERIFICATION: PASSED");
    console.log("Signature length:", signature.length, "chars");
    process.exit(0);
  } else {
    console.error("JWS VERIFICATION: FAILED - payload mismatch");
    process.exit(1);
  }
}

main().catch(err => { console.error("Error:", err.message); process.exit(1); });
