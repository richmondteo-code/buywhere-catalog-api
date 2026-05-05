"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const crypto_1 = __importDefault(require("crypto"));
const apiKey_1 = require("../middleware/apiKey");
const mcp_1 = require("./mcp");
const router = (0, express_1.Router)();
const taskStore = new Map();
const TASK_TTL_MS = 30 * 60 * 1000;
setInterval(() => {
    const cutoff = Date.now() - TASK_TTL_MS;
    for (const [id, task] of taskStore) {
        if (task.createdAt < cutoff)
            taskStore.delete(id);
    }
}, 5 * 60 * 1000).unref();
function jsonrpcOk(id, result) {
    return { jsonrpc: '2.0', id, result };
}
function jsonrpcErr(id, code, message) {
    return { jsonrpc: '2.0', id, error: { code, message } };
}
async function executeTask(method, params) {
    switch (method) {
        case 'tools/call': {
            const toolName = params.name;
            const toolArgs = (params.arguments && typeof params.arguments === 'object')
                ? params.arguments
                : {};
            if (!toolName)
                throw { code: -32602, message: 'Missing tool name' };
            const result = await (0, mcp_1.dispatchTool)(toolName, toolArgs);
            return { content: [{ type: 'text', text: JSON.stringify(result) }] };
        }
        default:
            throw { code: -32601, message: `Unknown method: ${method}` };
    }
}
router.post('/tasks/send', apiKey_1.requireApiKey, apiKey_1.checkRateLimit, async (req, res) => {
    const body = req.body;
    if (!body || body.jsonrpc !== '2.0' || !body.method) {
        return res.status(400).json(jsonrpcErr(body?.id ?? null, -32600, 'Invalid JSON-RPC 2.0 request'));
    }
    const { id, method } = body;
    const params = (body.params && typeof body.params === 'object' && !Array.isArray(body.params))
        ? body.params
        : {};
    const taskId = crypto_1.default.randomUUID();
    const task = { taskId, status: 'working', createdAt: Date.now() };
    taskStore.set(taskId, task);
    try {
        const result = await executeTask(method, params);
        task.status = 'completed';
        task.result = result;
        return res.json(jsonrpcOk(id, {
            id: taskId,
            taskId,
            status: 'completed',
            artifacts: result,
        }));
    }
    catch (err) {
        const e = err;
        task.status = 'failed';
        task.error = { code: e.code ?? -32603, message: e.message ?? 'Internal error' };
        return res.json(jsonrpcErr(id, task.error.code, task.error.message));
    }
});
router.post('/tasks/sendSubscribe', apiKey_1.requireApiKey, apiKey_1.checkRateLimit, async (req, res) => {
    const body = req.body;
    if (!body || body.jsonrpc !== '2.0' || !body.method) {
        return res.status(400).json(jsonrpcErr(body?.id ?? null, -32600, 'Invalid JSON-RPC 2.0 request'));
    }
    const { id, method } = body;
    const params = (body.params && typeof body.params === 'object' && !Array.isArray(body.params))
        ? body.params
        : {};
    const taskId = crypto_1.default.randomUUID();
    const task = { taskId, status: 'working', createdAt: Date.now() };
    taskStore.set(taskId, task);
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();
    const sendSSE = (event, data) => {
        res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
    };
    sendSSE('task_status', { taskId, status: 'working' });
    try {
        const result = await executeTask(method, params);
        task.status = 'completed';
        task.result = result;
        sendSSE('task_status', { taskId, status: 'completed' });
        sendSSE('task_result', { taskId, artifacts: result });
        res.end();
    }
    catch (err) {
        const e = err;
        task.status = 'failed';
        task.error = { code: e.code ?? -32603, message: e.message ?? 'Internal error' };
        sendSSE('task_status', { taskId, status: 'failed', error: task.error });
        res.end();
    }
    req.on('close', () => {
        if (task.status === 'working') {
            task.status = 'failed';
            task.error = { code: -32800, message: 'Client disconnected' };
        }
    });
});
router.get('/tasks/:taskId', apiKey_1.requireApiKey, apiKey_1.checkRateLimit, (req, res) => {
    const task = taskStore.get(req.params.taskId);
    if (!task)
        return res.status(404).json({ error: 'Task not found' });
    return res.json({
        id: task.taskId,
        taskId: task.taskId,
        status: task.status,
        ...(task.result ? { artifacts: task.result } : {}),
        ...(task.error ? { error: task.error } : {}),
        ...(task.progress ? { progress: { message: task.progress } } : {}),
    });
});
router.get('/tasks/:taskId/status', apiKey_1.requireApiKey, apiKey_1.checkRateLimit, (req, res) => {
    const task = taskStore.get(req.params.taskId);
    if (!task)
        return res.status(404).json({ error: 'Task not found' });
    return res.json({
        taskId: task.taskId,
        status: task.status,
        ...(task.progress ? { progress: { message: task.progress } } : {}),
    });
});
router.delete('/tasks/:taskId', apiKey_1.requireApiKey, apiKey_1.checkRateLimit, (req, res) => {
    const task = taskStore.get(req.params.taskId);
    if (!task)
        return res.status(404).json({ error: 'Task not found' });
    task.status = 'failed';
    task.error = { code: -32800, message: 'Task cancelled by client' };
    return res.json({ taskId: task.taskId, status: 'failed', message: 'Cancelled' });
});
router.get('/', (_req, res) => {
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
        methods: ['tools/call'],
        tools: ['search_products', 'get_product', 'compare_products', 'get_deals', 'list_categories', 'find_best_price'],
        auth: 'Bearer token — register at https://api.buywhere.ai/v1/auth/register',
    });
});
exports.default = router;
