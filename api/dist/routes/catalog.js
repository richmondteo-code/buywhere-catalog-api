"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const config_1 = require("../config");

const router = (0, express_1.Router)();

router.get('/stats', async (_req, res) => {
  try {
    const result = await config_1.db.query(`
      SELECT
        (SELECT reltuples::bigint FROM pg_class WHERE oid = 'public.products'::regclass) AS total_products,
        (SELECT reltuples::bigint FROM pg_class WHERE oid = 'public.merchants'::regclass) AS total_merchants
    `);

    const row = result.rows[0] || {};
    res.json({
      data: {
        total_products: Number(row.total_products || 0),
        total_merchants: Number(row.total_merchants || 0),
        active_products: Number(row.total_products || 0)
      },
      meta: {
        approximate: true,
        source: "pg_class_fallback",
        ts: new Date().toISOString()
      }
    });
  } catch (err) {
    console.error('[catalog/stats] fallback error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

exports.default = router;
