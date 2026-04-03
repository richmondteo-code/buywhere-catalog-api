import { NextRequest, NextResponse } from "next/server";
import { SESClient, SendEmailCommand } from "@aws-sdk/client-ses";
import { randomBytes } from "crypto";
import { readFileSync, writeFileSync, existsSync } from "fs";

const SES_REGION = process.env.AWS_REGION ?? "ap-southeast-1";
const FROM_EMAIL = process.env.SES_FROM_EMAIL ?? "noreply@buywhere.ai";
const KEYS_FILE = "/tmp/bw-api-keys.json";

function generateKey(): string {
  return "bw_beta_" + randomBytes(20).toString("hex");
}

interface KeyRecord {
  name: string;
  email: string;
  useCase: string;
  key: string;
  created_at: string;
  usage_count: number;
}

function loadKeys(): KeyRecord[] {
  if (!existsSync(KEYS_FILE)) return [];
  try {
    return JSON.parse(readFileSync(KEYS_FILE, "utf-8")) as KeyRecord[];
  } catch {
    return [];
  }
}

function saveKey(entry: KeyRecord) {
  const keys = loadKeys();
  keys.push(entry);
  try {
    writeFileSync(KEYS_FILE, JSON.stringify(keys, null, 2));
  } catch {
    // /tmp is ephemeral on Vercel — log and continue
    console.warn("Could not write keys file:", KEYS_FILE);
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const { name, email, useCase = "" } = body as {
    name?: string;
    email?: string;
    useCase?: string;
  };

  if (!name || !email) {
    return NextResponse.json(
      { error: "Name and email are required." },
      { status: 400 }
    );
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json(
      { error: "Invalid email address." },
      { status: 400 }
    );
  }

  const key = generateKey();
  const createdAt = new Date().toISOString();

  saveKey({ name, email, useCase, key, created_at: createdAt, usage_count: 0 });

  const emailBody = `Hi ${name},

Your BuyWhere API key is ready. You're on the free beta plan — no credit card required.

API Key:
${key}

Quick start (curl):

  curl "https://api.buywhere.ai/v1/search?q=wireless+headphones&limit=5" \\
    -H "Authorization: Bearer ${key}"

Full documentation: https://buywhere.ai/developers

Happy building,
The BuyWhere Team

---
Free during beta. Fair-use limits apply. Questions? hello@buywhere.ai
`;

  try {
    const ses = new SESClient({ region: SES_REGION });
    await ses.send(
      new SendEmailCommand({
        Source: FROM_EMAIL,
        Destination: { ToAddresses: [email] },
        Message: {
          Subject: { Data: "Your BuyWhere API key" },
          Body: { Text: { Data: emailBody } },
        },
      })
    );
  } catch (err) {
    // Email failure is non-fatal — key is still returned in the response
    console.error("SES send failed:", err);
  }

  return NextResponse.json({ key });
}
