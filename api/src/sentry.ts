import * as Sentry from '@sentry/node';
import type express from 'express';

export function initSentry() {
  const dsn = process.env.SENTRY_DSN;
  if (!dsn) {
    console.log('[sentry] SENTRY_DSN not set — error tracking disabled');
    return;
  }
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV || 'production',
    tracesSampleRate: 0.1,
    enableTracing: true,
  });
  console.log('[sentry] Error tracking initialized (env=%s)', process.env.NODE_ENV || 'production');
}

export function sentryRequestHandler(req: express.Request, _res: express.Response, next: express.NextFunction) {
  if (Sentry.getCurrentHub?.()?.getScope?.()) {
    const scope = Sentry.getCurrentHub().getScope();
    scope.setUser({
      ip_address: req.ip,
      id: (req as any).sessionId || undefined,
    });
    scope.setExtra('country', (req.query.country as string) || (req.body?.country as string) || '');
    scope.setTag('method', req.method);
    scope.setTag('path', req.path);
  }
  next();
}

export { Sentry };
