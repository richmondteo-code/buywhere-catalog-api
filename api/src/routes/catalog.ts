import { Router, Request, Response } from 'express';
import { db } from '../config';

const router = Router();

// GET /v1/catalog/stats — catalog-level aggregate statistics
// Unauthenticated — used by MCP server info, monitor, and discovery tools
router.get('/stats', async (_req: Request, res: Response) => {
  try {
    const productsResult = await db.query('SELECT COUNT(*)::int AS total FROM products');
    const totalProducts = parseInt(productsResult.rows[0].total, 10);

    let sourcesCount = 0;
    let recentCount = 0;
    let countriesCount = 0;
    try {
      const r = await db.query("SELECT COUNT(DISTINCT source)::int AS c FROM products WHERE is_active = true");
      sourcesCount = parseInt(r.rows[0].c, 10);
    } catch { /* column may not exist */ }

    try {
      const r = await db.query("SELECT COUNT(*)::int AS c FROM products WHERE is_active = true AND updated_at >= NOW() - INTERVAL '7 days'");
      recentCount = parseInt(r.rows[0].c, 10);
    } catch { /* column may not exist */ }

    try {
      const r = await db.query("SELECT COUNT(DISTINCT country_code)::int AS c FROM products WHERE is_active = true AND country_code IS NOT NULL");
      countriesCount = parseInt(r.rows[0].c, 10);
    } catch { /* column may not exist */ }

    let totalRegisteredMerchants = 0;
    try {
      const mr = await db.query('SELECT COUNT(*)::int AS c FROM merchants');
      totalRegisteredMerchants = parseInt(mr.rows[0].c, 10);
    } catch { /* merchants table may not exist */ }

    res.json({
      data: {
        total_products: totalProducts,
        total_merchants: sourcesCount,
        products_added_7d: recentCount,
        total_countries: countriesCount,
        total_registered_merchants: totalRegisteredMerchants,
      },
      meta: { ts: new Date().toISOString() },
    });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
