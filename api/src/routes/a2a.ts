import { Router, Request, Response } from 'express';
import crypto from 'crypto';
import { requireApiKey, checkRateLimit } from '../middleware/apiKey';
import { dispatchTool } from './mcp';

const router = Router();

interface TaskEntry {
  taskId: string;
  status: string;
  createdAt: number;
  result?: unknown;
  error?: { code: number; message: string };
  progress?: string;
}

const taskStore = new Map<string, TaskEntry>();
const TASK_TTL_MS = 30 * 60 * 1000;

setInterval(() => {
  const cutoff = Date.now() - TASK_TTL_MS;
  for (const [id, task] of taskStore) {
    if (task.createdAt < cutoff) taskStore.delete(id);
  }
}, 5 * 60 * 1000).unref();

function jsonrpcOk(id: unknown, result: unknown) {
  return { jsonrpc: '2.0', id, result };
}

function jsonrpcErr(id: unknown, code: number, message: string) {
  return { jsonrpc: '2.0', id, error: { code, message } };
}

function extractMessageText(params: Record<string, unknown>): string {
  try {
    const msg = params.message as Record<string, unknown>;
    const parts = msg.parts as Array<Record<string, unknown>>;
    return (parts[0]?.text as string) || '';
  } catch {
    return '';
  }
}

function routeIntent(text: string): { tool: string; args: Record<string, unknown> } {
  const lower = text.toLowerCase();

  if (/search|find/i.test(lower)) {
    const q = text.replace(/^(search|find)\s*(for\s*)?/i, '').trim() || text;
    return { tool: 'search_products', args: { q, limit: 10 } };
  }
  if (/match|equivalent/i.test(lower)) {
    const q = text.replace(/^(match|find equivalent of?)\s*/i, '').trim() || text;
    return { tool: 'search_products', args: { q: `${q} equivalent`, limit: 10 } };
  }
  if (/best.?price|cheapest/i.test(lower)) {
    const productName = text.replace(/^(best\s*price\s*for\s*|cheapest\s*|find\s*cheapest\s*)/i, '').trim();
    return { tool: 'find_best_price', args: { product_name: productName || text } };
  }
  if (/deal|discount/i.test(lower)) {
    return { tool: 'get_deals', args: { limit: 10, min_discount: 10 } };
  }
  if (/price|history/i.test(lower)) {
    const q = text.replace(/^(price\s*history\s*of\s*|price\s*of\s*)/i, '').trim() || text;
    return { tool: 'search_products', args: { q, limit: 5, compact: true } };
  }
  if (/categories|category/i.test(lower)) {
    return { tool: 'list_categories', args: {} };
  }

  return { tool: '', args: {} };
}

function capabilityDescription() {
  return "I can help you search products, find best prices, discover deals, match products across markets, and browse categories. Try asking: 'search for Dyson hair dryer', 'find the cheapest iPhone 16', or 'show me current deals'.";
}

async function executeTask(_method: string, params: Record<string, unknown>) {
  const text = extractMessageText(params);
  const { tool, args } = routeIntent(text);

  if (!tool) {
    return {
      intent: 'capability_description',
      content: [{ type: 'text', text: capabilityDescription() }],
    };
  }

  const result = await dispatchTool(tool, args);
  return {
    intent: tool,
    content: [{ type: 'json', text: JSON.stringify(result) }],
  };
}

router.post('/tasks/send', requireApiKey, checkRateLimit, async (req: Request, res: Response) => {
  const body = req.body;
  if (!body || body.jsonrpc !== '2.0' || !body.method) {
    return res.status(400).json(jsonrpcErr(body?.id ?? null, -32600, 'Invalid JSON-RPC 2.0 request'));
  }
  const { id, method } = body;
  const params = (body.params && typeof body.params === 'object' && !Array.isArray(body.params))
    ? body.params as Record<string, unknown>
    : {};
  const taskId = crypto.randomUUID();
  const task: TaskEntry = { taskId, status: 'working', createdAt: Date.now() };
  taskStore.set(taskId, task);
  try {
    const result = await executeTask(method, params);
    task.status = 'completed';
    task.result = result;
    return res.json(jsonrpcOk(id, {
      id: taskId,
      taskId,
      status: 'completed',
      artifacts: result.content,
    }));
  } catch (err: unknown) {
    const e = err as { code?: number; message?: string };
    task.status = 'failed';
    task.error = { code: e.code ?? -32603, message: e.message ?? 'Internal error' };
    return res.json(jsonrpcErr(id, task.error.code, task.error.message));
  }
});

router.post('/tasks/sendSubscribe', requireApiKey, checkRateLimit, async (req: Request, res: Response) => {
  const body = req.body;
  if (!body || body.jsonrpc !== '2.0' || !body.method) {
    return res.status(400).json(jsonrpcErr(body?.id ?? null, -32600, 'Invalid JSON-RPC 2.0 request'));
  }
  const { id: _id, method } = body;
  const params = (body.params && typeof body.params === 'object' && !Array.isArray(body.params))
    ? body.params as Record<string, unknown>
    : {};
  const taskId = crypto.randomUUID();
  const task: TaskEntry = { taskId, status: 'working', createdAt: Date.now() };
  taskStore.set(taskId, task);

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const sendSSE = (event: string, data: unknown) => {
    if (!res.writableEnded && !res.destroyed) {
      res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
    }
  };
  sendSSE('task_status', { taskId, status: 'working' });

  let aborted = false;
  req.on('close', () => {
    aborted = true;
    if (task.status === 'working') {
      task.status = 'failed';
      task.error = { code: -32800, message: 'Client disconnected' };
    }
  });
  res.on('error', () => {
    aborted = true;
    if (!res.destroyed) res.destroy();
  });

  try {
    const result = await executeTask(method, params);
    if (aborted) return;
    task.status = 'completed';
    task.result = result;
    sendSSE('task_status', { taskId, status: 'completed' });
    sendSSE('task_result', { taskId, artifacts: result.content });
    if (!res.writableEnded && !res.destroyed) res.end();
  } catch (err: unknown) {
    if (aborted) return;
    const e = err as { code?: number; message?: string };
    task.status = 'failed';
    task.error = { code: e.code ?? -32603, message: e.message ?? 'Internal error' };
    sendSSE('task_status', { taskId, status: 'failed', error: task.error });
    if (!res.writableEnded && !res.destroyed) res.end();
  }
});

router.get('/tasks/:taskId', requireApiKey, checkRateLimit, (req: Request, res: Response) => {
  const task = taskStore.get(req.params.taskId as string);
  if (!task) return res.status(404).json({ error: 'Task not found' });
  return res.json({
    id: task.taskId,
    taskId: task.taskId,
    status: task.status,
    ...(task.result ? { artifacts: task.result } : {}),
    ...(task.error ? { error: task.error } : {}),
    ...(task.progress ? { progress: { message: task.progress } } : {}),
  });
});

router.get('/tasks/:taskId/status', requireApiKey, checkRateLimit, (req: Request, res: Response) => {
  const task = taskStore.get(req.params.taskId as string);
  if (!task) return res.status(404).json({ error: 'Task not found' });
  return res.json({
    taskId: task.taskId,
    status: task.status,
    ...(task.progress ? { progress: { message: task.progress } } : {}),
  });
});

router.delete('/tasks/:taskId', requireApiKey, checkRateLimit, (req: Request, res: Response) => {
  const task = taskStore.get(req.params.taskId as string);
  if (!task) return res.status(404).json({ error: 'Task not found' });
  task.status = 'failed';
  task.error = { code: -32800, message: 'Task cancelled by client' };
  return res.json({ taskId: task.taskId, status: 'failed', message: 'Cancelled' });
});

router.get('/', (_req: Request, res: Response) => {
  res.json({
    name: 'buywhere-a2a',
    description: 'BuyWhere A2A (Agent-to-Agent) protocol endpoint. Implements task lifecycle per Google A2A spec.',
    protocol: 'a2a',
    protocolVersion: '1.0',
    transport: 'http+streaming',
    endpoints: {
      'POST /a2a/tasks/send': 'Execute a task synchronously. Accepts JSON-RPC 2.0 envelope with method and params.',
      'POST /a2a/tasks/sendSubscribe': 'Execute a task with SSE streaming for progress and result.',
      'GET /a2a/tasks/:taskId': 'Get task status and result.',
      'GET /a2a/tasks/:taskId/status': 'Lightweight task status check.',
      'DELETE /a2a/tasks/:taskId': 'Cancel a pending or in-progress task.',
    },
    methods: ['tools/call', 'tasks/send', 'tasks/sendSubscribe'],
    tools: ['search_products', 'get_product', 'compare_products', 'get_deals', 'list_categories', 'find_best_price'],
    auth: 'Bearer token — register at https://api.buywhere.ai/v1/auth/register',
  });
});

export default router;
