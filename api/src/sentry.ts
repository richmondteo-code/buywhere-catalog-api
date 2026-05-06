import * as Sentry from '@sentry/node';
<<<<<<< HEAD
import type { Request, Response, NextFunction } from 'express';
=======
import type express from 'express';
>>>>>>> a8194ee77 (fix(BUY-12731): use Cloud Run hostname + X-Forwarded-Host to fix 404 routing)

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
<<<<<<< HEAD
=======
    enableTracing: true,
>>>>>>> a8194ee77 (fix(BUY-12731): use Cloud Run hostname + X-Forwarded-Host to fix 404 routing)
  });
  console.log('[sentry] Error tracking initialized (env=%s)', process.env.NODE_ENV || 'production');
}

<<<<<<< HEAD
export function sentryRequestHandler(req: Request, _res: Response, next: NextFunction) {
  Sentry.setUser({
    ip_address: req.ip,
    id: (req as any).sessionId || undefined,
  });
  Sentry.setExtra('country', (req.query.country as string) || (req.body?.country as string) || '');
  Sentry.setTag('method', req.method);
  Sentry.setTag('path', req.path);
=======
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
>>>>>>> a8194ee77 (fix(BUY-12731): use Cloud Run hostname + X-Forwarded-Host to fix 404 routing)
  next();
}

export { Sentry };
