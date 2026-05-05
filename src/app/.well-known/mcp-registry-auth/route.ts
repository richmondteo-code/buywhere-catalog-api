import { NextResponse } from "next/server";

// DNS auth proof for MCP registry (BUY-11299)
// Public key (p=): JkMD3wRId8C8vMuw02YDk8XTJAXR8NxVf669jecpY68=
export function GET() {
  return new NextResponse(
    "v=MCPv1; k=ed25519; p=JkMD3wRId8C8vMuw02YDk8XTJAXR8NxVf669jecpY68=",
    {
      headers: {
        "Content-Type": "text/plain",
      },
    }
  );
}
