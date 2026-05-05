"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RE_ALERT_INTERVAL_MS = void 0;
exports.recordDown = recordDown;
exports.recordUp = recordUp;
exports.getSustainedDownMonitors = getSustainedDownMonitors;
exports.updateLastAlertAt = updateLastAlertAt;
exports.RE_ALERT_INTERVAL_MS = 30 * 60 * 1000; // 30 minutes
async function recordDown(_monitorID, _friendlyName, _url) {
    // Stub - uptime monitor state not yet implemented
}
async function recordUp(_monitorID) {
    // Stub - uptime monitor state not yet implemented
}
async function getSustainedDownMonitors() {
    return [];
}
async function updateLastAlertAt(_monitorID) {
    // Stub - uptime monitor state not yet implemented
}
