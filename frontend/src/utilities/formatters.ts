export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function formatPercent(pct: number): string {
  return `${pct.toFixed(1)}%`;
}

export function formatRatio(r: number): string {
  if (r === Infinity || r > 1000) return '∞×';
  return `${r.toFixed(2)}×`;
}

export function formatMs(ms: number): string {
  return `${ms.toFixed(1)} ms`;
}

export function formatSeconds(sec: number): string {
  return `${sec.toFixed(2)}s`;
}
