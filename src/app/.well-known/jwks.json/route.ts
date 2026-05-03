export function GET() {
  return Response.json({"keys":[{"kty":"EC","x":"8cFEffIG7qqs_PayCIrarXydnqRUZqgCXK4jRwXzcEE","y":"M4fMCRC48H5s_hFbbgzB0Kq-8KnFOILbom-zfdHswoc","crv":"P-256","kid":"buywhere-agent-card","alg":"ES256"}]}, {
    headers: {
      "Cache-Control": "public, max-age=86400",
    },
  });
}
