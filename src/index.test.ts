import { describe, it, expect } from "vitest";
import { formatTimecode, targetVideoBitrateKbps } from "./index";

describe("formatTimecode", () => {
  it("formats seconds as HH:MM:SS", () => {
    expect(formatTimecode(0)).toBe("00:00:00");
    expect(formatTimecode(65)).toBe("00:01:05");
    expect(formatTimecode(3661)).toBe("01:01:01");
  });
  it("clamps negatives to zero", () => {
    expect(formatTimecode(-10)).toBe("00:00:00");
  });
});

describe("targetVideoBitrateKbps", () => {
  it("computes a positive bitrate for a normal clip", () => {
    expect(targetVideoBitrateKbps(60, 25)).toBeGreaterThan(0);
  });
  it("reserves room for audio", () => {
    const noAudio = targetVideoBitrateKbps(60, 25, 0);
    const withAudio = targetVideoBitrateKbps(60, 25, 128);
    expect(noAudio - withAudio).toBe(128);
  });
  it("returns 0 for non-positive duration", () => {
    expect(targetVideoBitrateKbps(0, 25)).toBe(0);
  });
});
