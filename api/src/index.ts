import { initSentry } from './sentry';
import { createApp } from './server';
import { PORT } from './config';
import { shutdownPostHog } from './analytics/posthog';
import { runMigrations } from './migrate';

// Initialize Sentry before anything else so all errors are captured
initSentry();

const app = createApp();

runMigrations().catch(err => {
  console.error('Migration failed during startup:', err);
});

const server = app.listen(PORT, () => {
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
