import express from 'express';
import cors from 'cors';
import { Sentry } from './sentry';
import { agentDetectMiddleware, agentDiscoveryHeaders } from './middleware/agentDetect';
import authRouter from './routes/auth';
import keysRouter from './routes/keys';
import { requireApiKey } from './middleware/apiKey';
import productsRouter from './routes/products';
import categoriesRouter from './routes/categories';
import redirectRouter from './routes/redirect';
import wellknownRouter from './routes/wellknown';
import docsRouter from './routes/docs';
import pagesRouter from './routes/pages';
import publicCategoriesRouter from './routes/publicCategories';
import publicCompareRouter from './routes/publicCompare';
import compareSlugRouter from './routes/compareSlug';
import adminCompareRouter from './routes/adminCompare';
import mcpRouter from './routes/mcp';
import analyticsRouter from './routes/analytics';
import revenueRouter from './routes/revenue';
import sitemapCompareRouter from './routes/sitemapCompare';
import landingRouter from './routes/landing';
import clicksRouter from './routes/clicks';
import metricsRouter from './routes/metrics';
import developersRouter from './routes/developers';
import ingestRouter from './routes/ingest';
import { a2aRouter } from './routes/a2a';
import { db } from './config';

export function createApp() {
  const app = express();

  app.use(cors({
    origin: (process.env.CORS_ALLOWED_ORIGINS || 'https://us.buywhere.com,https://buywhere.ai').split(',').map((o) => o.trim()),
    credentials: true,
  }));
  app.use((_req, res, next) => {
    res.set('X-Content-Type-Options', 'nosniff');
    res.set('X-Frame-Options', 'DENY');
    next();
  });
  app.use(agentDiscoveryHeaders);
  app.use(agentDetectMiddleware);
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: false }));

  // Health check - fast in-process check as required by BUY-3280
  app.get('/health', (_req, res) => {
    res.json({
      status: 'ok',
      ts: new Date().toISOString(),
    });
  });

  // MCP / OpenAI plugin discovery
  app.use('/.well-known', wellknownRouter);
  app.get('/openapi.json', (req, res) => wellknownRouter(req, res, () => {}));

  // ChatGPT Actions-compatible OpenAPI spec (OpenAPI 3.1, action-friendly)
  app.get('/chatgpt-openapi.json', (_req, res) => {
    res.json(require('./routes/chatgpt-openapi.json'));
  });

  // AI crawler headers for public endpoints (Perplexity, GPTBot, etc.)
  const aiCrawlerHeaders = (_req: express.Request, res: express.Response, next: express.NextFunction) => {
    res.set('X-Robots-Tag', 'ai-index');
    res.set('Cache-Control', 'public, max-age=3600, s-maxage=86400');
    next();
  };

  // Docs
  app.use('/docs', aiCrawlerHeaders, docsRouter);

  // Public quickstart alias — launch fallback for BUY-3724
  // api.buywhere.ai/quickstart → /docs/guides/mcp
  app.get('/quickstart', aiCrawlerHeaders, (_req, res) => res.redirect(301, '/docs/guides/mcp'));

  // MCP JSON-RPC endpoint (Model Context Protocol)
  app.use('/mcp', mcpRouter);

  // A2A Agent-to-Agent protocol endpoint (Google A2A 1.0)
  app.use('/a2a', a2aRouter);

  // v1 API
  app.use('/v1/auth', authRouter);
  app.use('/v1/products', productsRouter);
  // v2 alias — same router, extends v1 contract with country_code + multi-region currency inference
  app.use('/v2/products', productsRouter);
  app.use('/v1/categories', categoriesRouter);
  app.use('/v1/developers', developersRouter);
  app.use('/v1/keys', keysRouter);
  // Scraper agent ingest compat: POST /v1/ingest/products (used by all scrapers)
  app.use('/v1/ingest', ingestRouter);

  // GET /v1/usage — daily usage for the authenticated developer
  app.get('/v1/usage', requireApiKey, async (req, res) => {
    const { id, tier } = req.apiKeyRecord!;
    const days = Math.min(parseInt((req.query.days as string) || '30'), 90);

    const [usageResult, tierResult] = await Promise.all([
      db.query(
        `SELECT date_trunc('day', created_at)::date AS day,
                COUNT(*) AS request_count
         FROM query_log
         WHERE api_key_id = $1
           AND created_at >= NOW() - ($2 || ' days')::interval
         GROUP BY day ORDER BY day DESC`,
        [id, days]
      ),
      db.query(
        `SELECT tier, rpm_limit, daily_limit FROM api_keys WHERE id = $1`,
        [id]
      ),
    ]);

    const dailyUsage = usageResult.rows.map((r: any) => ({
      day: r.day,
      request_count: parseInt(r.request_count),
    }));
    const total = dailyUsage.reduce((s: number, d: any) => s + d.request_count, 0);
    const limits = tierResult.rows[0] || {};
    const limit = parseInt(limits.daily_limit) || 1000;
    const today = dailyUsage.find((d: any) => d.day === new Date().toISOString().slice(0, 10));
    const todayTotal = today?.request_count || 0;

    res.json({
      daily_usage: dailyUsage,
      total,
      tier: limits.tier || tier,
      limit,
      usage_today: todayTotal,
      usage_remaining: Math.max(0, limit - todayTotal),
    });
  });

  // Backward-compat alias: /v1/search → /v1/products/search
  app.get("/v1/search", (req, res) => {
    const qs = req.url.includes("?") ? req.url.slice(req.url.indexOf("?")) : "";
    res.redirect(301, `/v1/products/search${qs}`);
  });
  app.use('/v1/analytics', analyticsRouter);
  app.use('/v1/revenue', revenueRouter);
  app.use('/v1/compare', aiCrawlerHeaders, compareSlugRouter);
  app.use('/api/v1/compare', aiCrawlerHeaders, compareSlugRouter); // alias — FE integration uses /api prefix

  // Admin editorial CRUD (ADMIN_API_KEY auth, not rate-limited)
  app.use('/admin/comparison-pages', adminCompareRouter);

  // Outbound click tracking (BUY-4869): /api/click redirect + /admin/clicks analytics
  app.use('/api', clicksRouter);
  app.use('/admin', clicksRouter);
  app.use('/admin', metricsRouter);

  // Affiliate redirect (no /v1 prefix — short URLs)
  app.use('/r', redirectRouter);

  // Public HTML pages with Schema.org JSON-LD (no auth — crawlable by AI agents)
  app.use('/p', aiCrawlerHeaders, pagesRouter);           // /p/:id — product page
  app.use('/c', aiCrawlerHeaders, publicCategoriesRouter); // /c/:slug — category page
  app.use('/compare', aiCrawlerHeaders, publicCompareRouter); // /compare?ids=id1,id2 — comparison page

  // Sitemaps
  app.use('/sitemap-compare.xml', sitemapCompareRouter);

  // Sitemap index — references all sitemaps
  app.get('/sitemap.xml', (req, res) => {
    const proto = ((req.headers['x-forwarded-proto'] as string) || req.protocol).split(',')[0].trim();
    const host = (req.headers['x-forwarded-host'] as string) || req.get('host') || 'buywhere.ai';
    const base = `${proto}://${host}`;
    const now = new Date().toISOString().slice(0, 10);
    const xml = [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      '  <sitemap>',
      `    <loc>${base}/sitemap-compare.xml</loc>`,
      `    <lastmod>${now}</lastmod>`,
      '  </sitemap>',
      '</sitemapindex>',
    ].join('\n');
    res.set('Content-Type', 'application/xml; charset=utf-8');
    res.set('Cache-Control', 'public, max-age=3600, s-maxage=86400');
    res.send(xml);
  });

  // GEO / AI-crawler discoverability
  app.get('/robots.txt', (_req, res) => {
    res.set('Content-Signal', 'ai-train=no, search=yes, ai-input=yes');
    res.type('text/plain').send(
      [
        'User-agent: *',
        'Allow: /',
        '',
        '# AI crawlers — explicitly allowed for GEO and LLM training/citations',
        'User-agent: GPTBot',
        'Allow: /',
        '',
        'User-agent: Claude-Web',
        'Allow: /',
        '',
        'User-agent: PerplexityBot',
        'Allow: /',
        '',
        'User-agent: Bytespider',
        'Allow: /',
        '',
        'User-agent: CCBot',
        'Allow: /',
        '',
        'User-agent: Applebot-Extended',
        'Allow: /',
        '',
        'User-agent: YouBot',
        'Allow: /',
        '',
        'User-agent: cohere-ai',
        'Allow: /',
        '',
        'Sitemap: https://buywhere.ai/sitemap.xml',
      ].join('\n')
    );
  });

  app.get('/llms.txt', (_req, res) => {
    res.set('X-Robots-Tag', 'ai-index');
    res.set('Cache-Control', 'public, max-age=86400');
    res.type('text/plain').send(
      `# BuyWhere\n\nBuyWhere is a structured product catalog and price comparison API for AI agents and LLM applications. We provide real-time pricing, availability, and product data from Singapore's major e-commerce platforms (Lazada, Shopee, Best Denki, and others).\n\n## What we offer\n- REST API: GET /v1/products, GET /v1/offers, GET /v1/categories\n- MCP endpoint: https://api.buywhere.ai/mcp\n- Schema.org-compatible product data (Product, Offer, ItemList)\n- Coverage: 2M+ Singapore products across 40+ merchants\n- Use cases: price comparison agents, shopping assistants, market research tools\n\n## Documentation\n- API docs: https://docs.buywhere.ai\n- MCP guide: https://api.buywhere.ai/docs/guides/mcp\n- GitHub: https://github.com/BuyWhere/buywhere\n\n## Licensing\nFree tier: 1,000 API calls/month. Commercial plans available.\n`
    );
  });

  // Landing pages — homepage (en_SG) and US edition (en_US)
  app.use(landingRouter);

  // 404 fallback
  app.use((_req, res) => {
    res.status(404).json({ error: 'Not found' });
  });

  // Sentry error capture — must be after all routes
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  app.use((err: Error, _req: express.Request, res: express.Response, next: express.NextFunction) => {
    Sentry.captureException(err);
    next(err);
  });

  return app;
}
