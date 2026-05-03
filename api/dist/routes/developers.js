"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const config_1 = require("../config");
const apiKey_1 = require("../middleware/apiKey");
const errors_1 = require("../middleware/errors");
const router = (0, express_1.Router)();
const TIER_LIMITS = {
    unverified: { rpm: 5, daily: 50 },
    free: { rpm: 60, daily: 1000 },
    pro: { rpm: 300, daily: 10000 },
    enterprise: { rpm: 1000, daily: 100000 },
};
function getTierDisplay(tier) {
    if (tier === 'enterprise')
        return 'enterprise';
    if (tier === 'pro')
        return 'pro';
    if (tier === 'unverified')
        return 'unverified';
    return 'free';
}
// GET /v1/developers/me
// Developer profile — requires API key auth
router.get('/me', apiKey_1.requireApiKey, async (req, res) => {
    const { id, agentName, tier } = req.apiKeyRecord;
    const result = await config_1.db.query(`SELECT email, created_at, email_verified FROM api_keys WHERE id = $1`, [id]);
    if (result.rows.length === 0) {
        (0, errors_1.sendError)(res, errors_1.ErrorCode.NOT_FOUND, 'Developer profile not found');
        return;
    }
    const row = result.rows[0];
    const limits = TIER_LIMITS[tier] ?? TIER_LIMITS.free;
    res.json({
        id,
        name: agentName,
        email: row.email,
        plan: getTierDisplay(tier),
        tier,
        created_at: row.created_at,
        email_verified: row.email_verified,
        rate_limit: {
            rpm: limits.rpm,
            daily: limits.daily,
        },
    });
});
// GET /v1/developers/me/usage
// Usage summary for the authenticated developer
router.get('/me/usage', apiKey_1.requireApiKey, async (req, res) => {
    const { id } = req.apiKeyRecord;
    const days = Math.min(parseInt(req.query.days || '30'), 90);
    const [usageResult, totalResult] = await Promise.all([
        config_1.db.query(`SELECT
         date_trunc('day', created_at)::date AS day,
         COUNT(*) AS request_count,
         COUNT(*) FILTER (WHERE status_code < 400) AS success_count,
         COUNT(*) FILTER (WHERE status_code >= 400) AS error_count
       FROM query_log
       WHERE api_key_id = $1
         AND created_at >= NOW() - ($2 || ' days')::interval
       GROUP BY day
       ORDER BY day DESC`, [id, days]),
        config_1.db.query(`SELECT
         COUNT(*) AS total_requests,
         COUNT(*) FILTER (WHERE status_code < 400) AS total_success,
         COUNT(*) FILTER (WHERE status_code >= 400) AS total_errors,
         ROUND(AVG(response_time_ms))::int AS avg_response_ms
       FROM query_log
       WHERE api_key_id = $1
         AND created_at >= NOW() - ($2 || ' days')::interval`, [id, days]),
    ]);
    const totals = totalResult.rows[0];
    const daily = usageResult.rows.map((r) => ({
        day: r.day,
        request_count: parseInt(r.request_count),
        success_count: parseInt(r.success_count),
        error_count: parseInt(r.error_count),
    }));
    res.json({
        daily_usage: daily,
        total_requests: parseInt(totals.total_requests),
        total_success: parseInt(totals.total_success),
        total_errors: parseInt(totals.total_errors),
        avg_response_ms: totals.avg_response_ms,
        period_days: days,
    });
});
exports.default = router;
