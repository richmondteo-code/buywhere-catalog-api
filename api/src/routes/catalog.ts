import { Router, Request, Response } from 'express';
import { db } from '../config';

const router = Router();

// GET /v1/catalog/stats — catalog-level aggregate statistics
// Unauthenticated — used by MCP server info, monitor, and discovery tools
// Uses pg_class estimates to avoid full table scan on 14M+ rows (BUY-13924)
router.get('/stats', async (_req: Request, res: Response) => {
  try {
    const result = await db.query(`
      SELECT
        (SELECT reltuples::bigint FROM pg_class WHERE oid = 'public.products'::regclass) AS total_products,
        (SELECT reltuples::bigint FROM pg_class WHERE oid = 'public.merchants'::regclass) AS total_merchants
    `);

    const row = result.rows[0] || {};
    res.json({
      data: {
        total_products: Number(row.total_products || 0),
        total_merchants: Number(row.total_merchants || 0),
        active_products: Number(row.total_products || 0),
      },
      meta: {
        approximate: true,
        source: 'pg_class_fallback',
        ts: new Date().toISOString(),
      },
    });
  } catch (err) {
    console.error('[catalog/stats] error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
