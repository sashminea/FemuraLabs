/** Format a number in degrees or mm. Uses a real minus sign and never shows "-0.00". */
export function fmt(v: number, digits = 2, signed = false): string {
  const f = Math.pow(10, digits);
  const r = Math.round(v * f) / f;
  if (r === 0) return (0).toFixed(digits);
  const body = Math.abs(r).toFixed(digits);
  if (r < 0) return `−${body}`;
  return signed ? `+${body}` : body;
}
