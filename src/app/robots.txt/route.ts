const robots = `User-agent: *
Allow: /

<<<<<<< HEAD
=======
User-agent: GPTBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: anthropic-ai
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: CCBot
Allow: /

>>>>>>> a8194ee77 (fix(BUY-12731): use Cloud Run hostname + X-Forwarded-Host to fix 404 routing)
Sitemap: https://buywhere.ai/sitemap.xml
Sitemap: https://buywhere.ai/sitemap-compare.xml
Sitemap: https://buywhere.ai/sitemap-products-sg.xml

<<<<<<< HEAD
Content-Signal: ai-train=no, search=yes, ai-input=yes
=======
LLMs-Txt: https://buywhere.ai/llms.txt
Agent-Card: https://buywhere.ai/.well-known/agent.json
>>>>>>> a8194ee77 (fix(BUY-12731): use Cloud Run hostname + X-Forwarded-Host to fix 404 routing)
`;

export function GET() {
  return new Response(robots, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
      "Content-Signal": "ai-train=no, search=yes, ai-input=yes",
    },
  });
}
