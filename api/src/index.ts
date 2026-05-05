import { initSentry, Sentry } from './sentry';
import { createApp } from './server';
import { PORT, db, redis } from './config';
import { shutdownPostHog } from './analytics/posthog';
import { runMigrations } from './migrate';

// Initialize Sentry before anything else so all errors are captured
initSentry();

process.on('uncaughtException', (err) => {
  console.error('[fatal] Uncaught exception:', err);
  Sentry.captureException(err, { tags: { type: 'uncaught_exception' } });
  fatalShutdown(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('[fatal] Unhandled rejection:', reason);
  const err = reason instanceof Error ? reason : new Error(String(reason));
  Sentry.captureException(err, { tags: { type: 'unhandled_rejection' } });
  fatalShutdown(1);
});

const app = createApp();

runMigrations().catch(err => {
  console.error('Migration failed during startup:', err);
  process.exit(1);
});

let server: ReturnType<typeof app.listen>;

async function fatalShutdown(exitCode: number) {
  console.log(`[fatal] Shutting down with code ${exitCode}...`);
  await shutdownPostHog();
  try { await db.end(); } catch {}
  redis.disconnect();
  if (server) {
    server.close(() => process.exit(exitCode));
  } else {
    process.exit(exitCode);
  }
  setTimeout(() => process.exit(exitCode), 5000).unref();
}

server = app.listen(PORT, () => {
  console.log(`BuyWhere API v1 listening on :${PORT}`);
  console.log(`  Health:   http://localhost:${PORT}/health`);
  console.log(`  Register: http://localhost:${PORT}/v1/auth/register`);
  console.log(`  Search:   http://localhost:${PORT}/v1/products/search`);
  console.log(`  MCP:      http://localhost:${PORT}/.well-known/ai-plugin.json`);
});

const shutdown = async () => {
  console.log('Shutting down...');
  await shutdownPostHog();
  server.close(() => process.exit(0));
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
