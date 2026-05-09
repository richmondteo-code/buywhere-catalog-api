import { Router, Request, Response } from 'express';
import { db, redis } from '../config';

const router = Router();

const STATS_CACHE_KEY = 'catalog:stats:v1';
const STATS_CACHE_TTL = 300; // 5 minutes

// GET /v1/catalog/stats — catalog-level aggregate statistics
// Unauthenticated — used by MCP server info, monitor, and discovery tools
router.get('/stats', async (_req: Request, res: Response) => {
  try {
    // Try Redis cache first — the underlying query is expensive on large tables
    try {
      const cached = await redis.get(STATS_CACHE_KEY);
      if (cached) {
        const data = JSON.parse(cached);
        res.json({ data, meta: { ts: new Date().toISOString(), cached: true } });
        return;
      }
    } catch {
      // Redis miss or unavailable — fall through to DB
    }

    // All queries use pg catalog stats (instant) — exact COUNT on 14M+ rows
    // exceeds statement_timeout even at 120s.
    const [approxTotal, approxDistinct, recentResult, merchantsResult] = await Promise.all([
      db.query(`SELECT reltuples::bigint AS estimate FROM pg_class WHERE relname = 'products'`),
      db.query(`
        SELECT attname, n_distinct
        FROM pg_stats
        WHERE tablename = 'products' AND attname IN ('source', 'country_code')
      `),
      // 7-day count — uses partial index idx_products_active_updated if available,
      // falls back gracefully on timeout
      db.query(`SELECT COUNT(*)::int AS cnt FROM products WHERE is_active = true AND updated_at >= NOW() - INTERVAL '7 days'`)
        .catch(() => ({ rows: [{ cnt: 0 }] })),
      db.query('SELECT COUNT(*)::int AS count FROM merchants')
        .catch(() => ({ rows: [{ count: 0 }] })),
    ]);

    const distinctMap: Record<string, number> = {};
    for (const row of approxDistinct.rows) {
      distinctMap[row.attname] = Math.round(Math.abs(row.n_distinct));
    }

    const data = {
      total_products: Number(approxTotal.rows[0]?.estimate || 0),
      total_merchants: distinctMap['source'] || 0,
      products_added_7d: recentResult.rows[0].cnt,
      total_countries: distinctMap['country_code'] || 0,
      total_registered_merchants: merchantsResult.rows[0].count,
    };

    // Cache in Redis
    try {
      await redis.set(STATS_CACHE_KEY, JSON.stringify(data), 'EX', STATS_CACHE_TTL);
    } catch {
      // cache write failure is non-fatal
    }

    res.json({ data, meta: { ts: new Date().toISOString(), cached: false } });
  } catch (err) {
    console.error('[catalog/stats] error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
