"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const config_1 = require("../config");
const router = (0, express_1.Router)();
// GET /v1/catalog/stats — catalog-level aggregate statistics
// Unauthenticated — used by MCP server info, monitor, and discovery tools
router.get('/stats', async (_req, res) => {
    try {
        const result = await config_1.db.query(`
      SELECT
        (SELECT COUNT(*) FROM products WHERE is_active = true)::int AS total_products,
        (SELECT COUNT(DISTINCT source) FROM products WHERE is_active = true)::int AS total_merchants,
        (SELECT COUNT(*) FROM products WHERE is_active = true AND updated_at >= NOW() - INTERVAL '7 days')::int AS products_added_7d,
        (SELECT COUNT(DISTINCT country_code) FROM products WHERE is_active = true AND country_code IS NOT NULL)::int AS total_countries,
        (SELECT COUNT(*) FROM merchants)::int AS total_registered_merchants
    `);
        const stats = result.rows[0];
        res.json({
            data: {
                total_products: stats.total_products,
                total_merchants: stats.total_merchants,
                products_added_7d: stats.products_added_7d,
                total_countries: stats.total_countries,
                total_registered_merchants: stats.total_registered_merchants,
            },
            meta: { ts: new Date().toISOString() },
        });
    }
    catch (err) {
        console.error('[catalog/stats] error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});
exports.default = router;
