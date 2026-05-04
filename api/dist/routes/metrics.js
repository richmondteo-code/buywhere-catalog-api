"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const config_1 = require("../config");
const router = (0, express_1.Router)();
const ADMIN_API_KEY = process.env.ADMIN_API_KEY;
function requireAdminKey(req, res, next) {
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
router.get('/', requireAdminKey, async (_req, res) => {
    try {
        const result = await config_1.db.query(`
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
    }
    catch (err) {
        console.error('[metrics] query error:', err);
        res.status(500).json({ error: 'Query failed', detail: String(err) });
    }
});
router.use((err, _req, res, _next) => {
    console.error('[metrics] error:', err);
    res.status(500).json({ error: err.message || 'Internal server error' });
});
exports.default = router;
