/** Video helpers — starter utilities for videoboost. */

/** Format a number of seconds as HH:MM:SS (negatives clamp to zero). */
export function formatTimecode(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const hh = Math.floor(s / 3600);
  const mm = Math.floor((s % 3600) / 60);
  const ss = s % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(hh)}:${pad(mm)}:${pad(ss)}`;
}

/**
 * Estimate the average video bitrate (kbps) needed to fit a clip of
 * `durationSeconds` into `targetSizeMB`, reserving `audioKbps` for audio.
 */
export function targetVideoBitrateKbps(
  durationSeconds: number,
  targetSizeMB: number,
  audioKbps = 128,
): number {
  if (durationSeconds <= 0) return 0;
  const totalKbits = targetSizeMB * 8 * 1024; // MB -> kbit
  const videoKbps = totalKbits / durationSeconds - audioKbps;
  return Math.max(0, Math.round(videoKbps));
}
