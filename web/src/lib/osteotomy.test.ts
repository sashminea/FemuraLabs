import { describe, it, expect } from "vitest";
import {
  wedgeGap,
  newMPTA,
  newHKA,
  wedgeVolume,
  correctionStatus,
} from "./osteotomy";

describe("osteotomy geometry", () => {
  it("computes the wedge gap for case05 (70 mm, 8 deg)", () => {
    // tan(8 deg) = 0.14054... -> 70 * 0.14054 = 9.8378
    expect(wedgeGap(70, 8)).toBeCloseTo(9.84, 2);
  });

  it("computes the wedge gap for a standard target (75 mm, 5 deg)", () => {
    // tan(5 deg) = 0.08748... -> 75 * 0.08748 = 6.561
    expect(wedgeGap(75, 5)).toBeCloseTo(6.56, 2);
  });

  it("returns zero for zero angle or width", () => {
    expect(wedgeGap(70, 0)).toBe(0);
    expect(wedgeGap(0, 8)).toBe(0);
  });

  it("updates MPTA correctly", () => {
    expect(newMPTA(86.13, 8)).toBeCloseTo(94.13, 2);
  });

  it("updates HKA correctly", () => {
    // Case05 pre-op HKA is +5.88 deg (varus)
    // 8 deg medial opening reduces varus by 8 deg -> -2.12 deg (valgus)
    expect(newHKA(5.88, 8)).toBeCloseTo(-2.12, 2);
  });

  it("calculates wedge volume correctly", () => {
    // 0.5 * 9.8378 * 70 * 50 = 17216 mm^3
    expect(wedgeVolume(70, 50, 8)).toBeCloseTo(17216, 0);
  });

  it("detects correction status", () => {
    // target is -3 to 0 deg (valgus to neutral)
    expect(correctionStatus(5.88)).toBe("under");  // still varus
    expect(correctionStatus(-1.5)).toBe("target"); // in valgus range
    expect(correctionStatus(-5.0)).toBe("over");   // too much valgus
  });
});
