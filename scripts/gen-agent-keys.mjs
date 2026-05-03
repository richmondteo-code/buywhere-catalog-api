import * as jose from "jose";
import fs from "fs";
import path from "path";

const PRIVATE_DIR = path.resolve("private");

async function main() {
  fs.mkdirSync(PRIVATE_DIR, { recursive: true });

  const { publicKey, privateKey } = await jose.generateKeyPair("ES256", { extractable: true });

  const privateKeyPem = await jose.exportPKCS8(privateKey);
  fs.writeFileSync(path.join(PRIVATE_DIR, "agent-key.pem"), privateKeyPem, "utf-8");
  fs.chmodSync(path.join(PRIVATE_DIR, "agent-key.pem"), 0o600);
  console.log("Wrote private/agent-key.pem");

  const publicJwk = await jose.exportJWK(publicKey);
  publicJwk.kid = "buywhere-agent-card";
  publicJwk.alg = "ES256";

  const jwks = { keys: [publicJwk] };
  fs.writeFileSync(path.join(PRIVATE_DIR, "agent-jwks.json"), JSON.stringify(jwks, null, 2) + "\n", "utf-8");
  console.log("Wrote private/agent-jwks.json");

  console.log("Key generation complete.");
}

main().catch(console.error);
