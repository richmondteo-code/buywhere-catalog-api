import express from 'express';

type Handler = (this: unknown, ...args: unknown[]) => unknown;

const PATCH_FLAG = Symbol.for('buywhere.expressAsyncPatch');
const METHOD_NAMES = ['use', 'all', 'get', 'post', 'put', 'patch', 'delete', 'options', 'head'] as const;

function isPromiseLike(value: unknown): value is Promise<unknown> {
  return !!value && typeof (value as Promise<unknown>).then === 'function';
}

function wrapHandler(handler: Handler): Handler {
  if (handler.length === 4) {
    return handler;
  }

  return function wrappedHandler(this: unknown, ...args: unknown[]) {
    const next = args[2];

    try {
      const result = handler.apply(this, args);
      if (typeof next === 'function' && isPromiseLike(result)) {
        result.catch(next as (reason: unknown) => PromiseLike<never>);
      }
      return result;
    } catch (error) {
      if (typeof next === 'function') {
        next(error);
        return;
      }
      throw error;
    }
  };
}

function wrapArg(arg: unknown): unknown {
  if (Array.isArray(arg)) {
    return arg.map(wrapArg);
  }
  if (typeof arg === 'function') {
    return wrapHandler(arg as Handler);
  }
  return arg;
}

export function patchExpressAsyncHandlers(): void {
  const routerProto = Object.getPrototypeOf(express.Router());
  if ((routerProto as Record<PropertyKey, unknown>)[PATCH_FLAG]) {
    return;
  }

  for (const methodName of METHOD_NAMES) {
    const original = routerProto[methodName] as ((...args: unknown[]) => unknown) | undefined;
    if (typeof original !== 'function') {
      continue;
    }

    routerProto[methodName] = function patchedMethod(...args: unknown[]) {
      return original.apply(this, args.map(wrapArg));
    };
  }

  (routerProto as Record<PropertyKey, unknown>)[PATCH_FLAG] = true;
}

patchExpressAsyncHandlers();
