/**
 * Safe formatting utilities for RazorShield AI console
 */

export function formatTimestamp(ts?: number | string | null): string {
  if (ts === undefined || ts === null || ts === '') {
    return new Date().toISOString().substring(11, 19);
  }
  const num = typeof ts === 'string' ? parseFloat(ts) : Number(ts);
  if (isNaN(num) || !isFinite(num)) {
    return new Date().toISOString().substring(11, 19);
  }
  // If timestamp is in seconds (< 10^11), convert to milliseconds
  const ms = num < 10000000000 ? num * 1000 : num;
  const d = new Date(ms);
  if (isNaN(d.getTime())) {
    return new Date().toISOString().substring(11, 19);
  }
  return d.toISOString().substring(11, 19);
}

export function formatDateTime(ts?: number | string | null): string {
  if (ts === undefined || ts === null || ts === '') {
    return new Date().toLocaleString();
  }
  const num = typeof ts === 'string' ? parseFloat(ts) : Number(ts);
  if (isNaN(num) || !isFinite(num)) {
    return new Date().toLocaleString();
  }
  const ms = num < 10000000000 ? num * 1000 : num;
  const d = new Date(ms);
  if (isNaN(d.getTime())) {
    return new Date().toLocaleString();
  }
  return d.toLocaleString();
}
