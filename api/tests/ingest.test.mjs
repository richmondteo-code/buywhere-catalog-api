import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'http';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

describe('ingest router', () => {
  let server;
  let port;
  let config;

  before(async () => {
    process.env.REDIS_HOST = '127.0.0.1';
    process.env.REDIS_PORT = '1';
    process.env.DATABASE_URL = 'postgresql://127.0.0.1:1/buywhere';

    const express = require('express');
    const ingestRouter = require('../dist/routes/ingest').default;
    config = require('../dist/config');

    const app = express();
    app.use('/v1/ingest', ingestRouter);
    server = http.createServer(app);
    await new Promise((resolve) => server.listen(0, resolve));
    port = server.address().port;
  });

  after(() => {
    server?.close();
    config?.redis?.disconnect?.();
    config?.db?.end?.().catch?.(() => {});
  });

  it('fails closed on GET /v1/ingest/health without an API key', async () => {
    const res = await fetch(`http://localhost:${port}/v1/ingest/health`);
    const body = await res.json();

    assert.equal(res.status, 401);
    assert.equal(body.error.code, 'MISSING_API_KEY');
  });
});
