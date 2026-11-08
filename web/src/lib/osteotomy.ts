/**
 * Geometric calculations for a high tibial osteotomy (HTO).
 * Pure functions, no React, no Three.js.
 */

export function wedgeGap(plateauWidthMm: number, thetaDeg: number): number {
  if (plateauWidthMm < 0 || thetaDeg < 0) return 0;
  return plateauWidthMm * Math.tan((thetaDeg * Math.PI) / 180);
}

export function newMPTA(preMPTADeg: number, thetaDeg: number): number {
  return preMPTADeg + thetaDeg;
}

export function newHKA(preHKADeg: number, thetaDeg: number): number {
  return preHKADeg - thetaDeg;
}

export function wedgeVolume(
  plateauWidthMm: number,
  apDepthMm: number,
  thetaDeg: number
): number {
  const g = wedgeGap(plateauWidthMm, thetaDeg);
  return 0.5 * g * plateauWidthMm * apDepthMm;
}

export function correctionStatus(
  newHKADeg: number,
  targetMinDeg = -3,
  targetMaxDeg = 0
): "under" | "target" | "over" {
  if (newHKADeg > targetMaxDeg) return "under";
  if (newHKADeg < targetMinDeg) return "over";
  return "target";
}
