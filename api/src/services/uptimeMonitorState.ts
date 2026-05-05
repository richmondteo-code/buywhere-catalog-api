export const RE_ALERT_INTERVAL_MS = 30 * 60 * 1000; // 30 minutes

export async function recordDown(
  _monitorID: string,
  _friendlyName: string,
  _url: string,
): Promise<void> {
  // Stub - uptime monitor state not yet implemented
}

export async function recordUp(_monitorID: string): Promise<void> {
  // Stub - uptime monitor state not yet implemented
}

export async function getSustainedDownMonitors(): Promise<any[]> {
  return [];
}

export async function updateLastAlertAt(_monitorID: string): Promise<void> {
  // Stub - uptime monitor state not yet implemented
}
