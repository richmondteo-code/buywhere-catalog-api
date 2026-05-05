"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const sentry_1 = require("./sentry");
const server_1 = require("./server");
const config_1 = require("./config");
const posthog_1 = require("./analytics/posthog");
const migrate_1 = require("./migrate");
// Initialize Sentry before anything else so all errors are captured
(0, sentry_1.initSentry)();
process.on('uncaughtException', (err) => {
    console.error('[fatal] Uncaught exception:', err);
    sentry_1.Sentry.captureException(err, { tags: { type: 'uncaught_exception' } });
    fatalShutdown(1);
});
process.on('unhandledRejection', (reason) => {
    console.error('[fatal] Unhandled rejection:', reason);
    const err = reason instanceof Error ? reason : new Error(String(reason));
    sentry_1.Sentry.captureException(err, { tags: { type: 'unhandled_rejection' } });
    fatalShutdown(1);
});
const app = (0, server_1.createApp)();
(0, migrate_1.runMigrations)().catch(err => {
    console.error('Migration failed during startup:', err);
    process.exit(1);
});
let server;
async function fatalShutdown(exitCode) {
    console.log(`[fatal] Shutting down with code ${exitCode}...`);
    await (0, posthog_1.shutdownPostHog)();
    try {
        await config_1.db.end();
    }
    catch { }
    config_1.redis.disconnect();
    if (server) {
        server.close(() => process.exit(exitCode));
    }
    else {
        process.exit(exitCode);
    }
    setTimeout(() => process.exit(exitCode), 5000).unref();
}
server = app.listen(config_1.PORT, () => {
    console.log(`BuyWhere API v1 listening on :${config_1.PORT}`);
    console.log(`  Health:   http://localhost:${config_1.PORT}/health`);
    console.log(`  Register: http://localhost:${config_1.PORT}/v1/auth/register`);
    console.log(`  Search:   http://localhost:${config_1.PORT}/v1/products/search`);
    console.log(`  MCP:      http://localhost:${config_1.PORT}/.well-known/ai-plugin.json`);
});
const shutdown = async () => {
    console.log('Shutting down...');
    await (0, posthog_1.shutdownPostHog)();
    server.close(() => process.exit(0));
};
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
