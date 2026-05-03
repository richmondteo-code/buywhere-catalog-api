import { Router, Request, Response, NextFunction } from 'express';
import { db } from '../config';

const router = Router();

const ADMIN_API_KEY = process.env.ADMIN_API_KEY;

function requireAdminKey(req: Request, res: Response, next: NextFunction): void {
  if (!ADMIN_API_KEY) {
    res.status(503).json({ error: 'Admin API not configured' });
    return;
  }
  const auth = req.headers['authorization'] || '';
  const key = auth.startsWith('Bearer ') ? auth.slice(7).trim() : '';
  if (!key || key !== ADMIN_API_KEY) {
    res.status(401).json({ error: 'Admin API key required' });
    return;
  }
  next();
}

// GET /admin/metrics — system-wide KPI counts
router.get('/metrics', requireAdminKey, async (_req: Request, res: Response) => {
  try {
    const result = await db.query(`
      SELECT
        (SELECT COUNT(*) FROM products WHERE is_active = true)::int AS total_products,
        (SELECT COUNT(*) FROM merchants)::int AS total_merchants,
        (SELECT COUNT(DISTINCT source) FROM products WHERE is_active = true)::int AS total_platforms
    `);
    const { total_products, total_merchants, total_platforms } = result.rows[0];
    res.json({
      total_products,
      total_merchants,
      total_platforms,
      ts: new Date().toISOString(),
    });
  } catch (err) {
    console.error('[metrics] query error:', err);
    res.status(500).json({ error: 'Query failed', detail: String(err) });
  }
});

// GET /admin/metrics/snapshots — historical KPI snapshot data (BUY-8975)
router.get('/metrics/snapshots', requireAdminKey, async (req: Request, res: Response) => {
  try {
    const days = Math.min(Math.max(parseInt(req.query.days as string) || 30, 1), 365);
    const result = await db.query(
      `SELECT product_count, merchant_count, platform_count, snapshot_at
       FROM kpi_snapshots
       WHERE snapshot_at >= NOW() - ($1 || ' days')::interval
       ORDER BY snapshot_at DESC`,
      [String(days)]
    );
    res.json({ snapshots: result.rows });
  } catch (err) {
    console.error('[metrics] snapshots query error:', err);
    res.status(500).json({ error: 'Query failed', detail: String(err) });
  }
});

router.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('[metrics] error:', err);
  res.status(500).json({ error: err.message || 'Internal server error' });
});

export default router;
