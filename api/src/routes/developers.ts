import { Router, Request, Response } from 'express';
import { db } from '../config';
import { requireApiKey } from '../middleware/apiKey';
import { sendError, ErrorCode } from '../middleware/errors';

const router = Router();

const TIER_LIMITS: Record<string, { rpm: number; daily: number }> = {
  unverified: { rpm: 5, daily: 50 },
  free: { rpm: 60, daily: 1000 },
  pro: { rpm: 300, daily: 10000 },
  enterprise: { rpm: 1000, daily: 100000 },
};

function getTierDisplay(tier: string): string {
  if (tier === 'enterprise') return 'enterprise';
  if (tier === 'pro') return 'pro';
  if (tier === 'unverified') return 'unverified';
  return 'free';
}

// GET /v1/developers/me
// Developer profile — requires API key auth
router.get('/me', requireApiKey, async (req: Request, res: Response) => {
  const { id, agentName, tier } = req.apiKeyRecord!;

  const result = await db.query(
    `SELECT email, created_at, email_verified FROM api_keys WHERE id = $1`,
    [id]
  );

  if (result.rows.length === 0) {
    sendError(res, ErrorCode.NOT_FOUND, 'Developer profile not found');
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
router.get('/me/usage', requireApiKey, async (req: Request, res: Response) => {
  const { id } = req.apiKeyRecord!;

  const days = Math.min(parseInt((req.query.days as string) || '30'), 90);

  const [usageResult, totalResult] = await Promise.all([
    db.query(
      `SELECT
         date_trunc('day', created_at)::date AS day,
         COUNT(*) AS request_count,
         COUNT(*) FILTER (WHERE status_code < 400) AS success_count,
         COUNT(*) FILTER (WHERE status_code >= 400) AS error_count
       FROM query_log
       WHERE api_key_id = $1
         AND created_at >= NOW() - ($2 || ' days')::interval
       GROUP BY day
       ORDER BY day DESC`,
      [id, days]
    ),
    db.query(
      `SELECT
         COUNT(*) AS total_requests,
         COUNT(*) FILTER (WHERE status_code < 400) AS total_success,
         COUNT(*) FILTER (WHERE status_code >= 400) AS total_errors,
         ROUND(AVG(response_time_ms))::int AS avg_response_ms
       FROM query_log
       WHERE api_key_id = $1
         AND created_at >= NOW() - ($2 || ' days')::interval`,
      [id, days]
    ),
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

export default router;
