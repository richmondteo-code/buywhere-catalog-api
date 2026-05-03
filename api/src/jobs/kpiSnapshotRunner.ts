import { db, redis } from '../config';
import { takeKpiSnapshot } from './kpiSnapshot';

const HOUR_UTC = parseInt(process.env.KPI_SNAPSHOT_HOUR_UTC ?? '17', 10);
const MIN_UTC  = parseInt(process.env.KPI_SNAPSHOT_MIN_UTC  ?? '0',  10);

function msUntilNext(hourUtc: number, minUtc: number): number {
  const now  = new Date();
  const next = new Date(now);
  next.setUTCHours(hourUtc, minUtc, 0, 0);
  if (next <= now) {
    next.setUTCDate(next.getUTCDate() + 1);
  }
  return next.getTime() - now.getTime();
}

function formatDelay(ms: number): string {
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  return `${h}h ${m}m`;
}

async function tick(): Promise<void> {
  console.log('[kpi-snapshot-runner] Job triggered');
  try {
    const snapshot = await takeKpiSnapshot();
    console.log(
      `[kpi-snapshot-runner] Completed — products: ${snapshot.product_count}, ` +
      `merchants: ${snapshot.merchant_count}, platforms: ${snapshot.platform_count}`
    );
  } catch (err) {
    console.error('[kpi-snapshot-runner] Unhandled job error:', err);
  }
  schedule();
}

function schedule(): void {
  const delay = msUntilNext(HOUR_UTC, MIN_UTC);
  console.log(
    `[kpi-snapshot-runner] Next run at ${HOUR_UTC.toString().padStart(2, '0')}:${MIN_UTC.toString().padStart(2, '0')} UTC ` +
    `(01:00 SGT) — in ${formatDelay(delay)}`
  );
  setTimeout(tick, delay);
}

async function main(): Promise<void> {
  console.log(
    `[kpi-snapshot-runner] Starting. Schedule: daily ${HOUR_UTC.toString().padStart(2, '0')}:${MIN_UTC.toString().padStart(2, '0')} UTC (01:00 SGT)`
  );

  const shutdown = async (sig: string) => {
    console.log(`[kpi-snapshot-runner] Received ${sig}, shutting down`);
    await db.end().catch(() => {});
    redis.disconnect();
    process.exit(0);
  };
  process.on('SIGTERM', () => void shutdown('SIGTERM'));
  process.on('SIGINT',  () => void shutdown('SIGINT'));

  schedule();
}

main().catch((err) => {
  console.error('[kpi-snapshot-runner] Fatal startup error:', err);
  process.exit(1);
});
