"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.takeKpiSnapshot = takeKpiSnapshot;
const config_1 = require("../config");
async function takeKpiSnapshot() {
    const result = await config_1.db.query(`
    SELECT
      (SELECT COUNT(*) FROM products WHERE is_active = true)::int AS product_count,
      (SELECT COUNT(*) FROM merchants)::int AS merchant_count,
      (SELECT COUNT(DISTINCT source) FROM products WHERE is_active = true)::int AS platform_count
  `);
    const { product_count, merchant_count, platform_count } = result.rows[0];
    const snapshot_at = new Date();
    await config_1.db.query(`INSERT INTO kpi_snapshots (product_count, merchant_count, platform_count, snapshot_at)
     VALUES ($1, $2, $3, $4)`, [product_count, merchant_count, platform_count, snapshot_at]);
    console.log(`[kpi-snapshot] Recorded — products: ${product_count}, merchants: ${merchant_count}, platforms: ${platform_count}`);
    return { product_count, merchant_count, platform_count, snapshot_at };
}
