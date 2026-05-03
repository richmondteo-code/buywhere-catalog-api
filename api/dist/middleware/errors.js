"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ErrorCode = void 0;
exports.sendError = sendError;
exports.sendRateLimitError = sendRateLimitError;
var ErrorCode;
(function (ErrorCode) {
    ErrorCode["MISSING_API_KEY"] = "MISSING_API_KEY";
    ErrorCode["INVALID_API_KEY"] = "INVALID_API_KEY";
    ErrorCode["REVOKED_API_KEY"] = "REVOKED_API_KEY";
    ErrorCode["NOT_FOUND"] = "NOT_FOUND";
    ErrorCode["RATE_LIMITED"] = "RATE_LIMITED";
    ErrorCode["INTERNAL_ERROR"] = "INTERNAL_ERROR";
})(ErrorCode || (exports.ErrorCode = ErrorCode = {}));
function sendError(res, code, message) {
    const statusMap = {
        MISSING_API_KEY: 401,
        INVALID_API_KEY: 403,
        REVOKED_API_KEY: 403,
        NOT_FOUND: 404,
        RATE_LIMITED: 429,
        INTERNAL_ERROR: 500,
    };
    const status = statusMap[code] || 500;
    res.status(status).json({ error: code, message: message || code });
}
function sendRateLimitError(res, retryAfter, limit, _remaining, message) {
    res.set('Retry-After', String(retryAfter));
    res.set('X-RateLimit-Limit', String(limit));
    res.set('X-RateLimit-Reset', String(Math.ceil(Date.now() / 1000) + retryAfter));
    res.status(429).json({ error: ErrorCode.RATE_LIMITED, message });
}
