"use client";

import { useEffect } from "react";

type Fx = "contour" | "rings";

const ZONES: Array<[string, Fx]> = [
  ["#hero", "contour"],
  ["#oss", "rings"],
];

const GLOW_SELECTOR = [
  "h1",
  "h2",
  "[data-cursor='text']",
  "#stats b",
  "#marquee span",
  "#pipeline svg",
  "#bento svg",
  "#proof b",
  "#proof td",
  "#cli button[role='tab']",
  "#oss a",
  "#problem p",
  "#problem h3",
  "#problem li",
  "#limits h3",
  "#limits p",
].join(",");

export function CursorEffects() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

    const BL = "77,163,255";
    const WH = "236,235,230";
    const TAU = Math.PI * 2;
    const GA = 1;

    const cv = document.createElement("canvas");
    cv.className = "cfx";
    cv.setAttribute("aria-hidden", "true");
    document.body.insertBefore(cv, document.body.firstChild);
    const ctx = cv.getContext("2d");
    if (!ctx) return;

    let W = 0;
    let H = 0;
    const rs = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = window.innerWidth;
      H = window.innerHeight;
      cv.width = Math.round(W * dpr);
      cv.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    rs();
    window.addEventListener("resize", rs);

    const rg = (a: number) => `rgba(${BL},${a.toFixed(3)})`;
    const rw = (a: number) => `rgba(${WH},${a.toFixed(3)})`;
    const sm = (v: number) => v * v * (3 - 2 * v);

    let T = 0;
    let dt = 16;
    let tx = 0;
    let ty = 0;
    let cx = 0;
    let cy = 0;
    let pvx = 0;
    let pvy = 0;
    let vis = 0;
    let target = 0;
    let seen = false;
    let run = false;
    let last = 0;
    let maxN = 0;

    const FX_KEYS: Fx[] = ["contour", "rings"];
    const WT: Record<Fx, number> = { contour: 0, rings: 0 };

    const Z = ZONES.map(([sel, k]) => {
      const el = document.querySelector(sel) as HTMLElement | null;
      return el ? { el, k } : null;
    }).filter((x): x is { el: HTMLElement; k: Fx } => x !== null);

    const FE = 150;

    const N = 44;
    const V = new Float32Array(N * N);
    const LV = [-0.9, -0.6, -0.3, 0, 0.3, 0.6, 0.9, 1.2];
    const fld = (px: number, py: number) =>
      0.55 *
        Math.sin(px * 0.0105 + 1.3 + T * 0.00007) *
        Math.cos(py * 0.0132 - 0.7) +
      0.35 * Math.sin((px + py) * 0.0071 + 2.1) +
      0.25 * Math.cos(px * 0.021 - py * 0.017 + T * 0.00005);

    const contour = (a: number) => {
      const cs = 12;
      const R = 250;
      const gx = Math.floor((cx - R) / cs) * cs;
      const gy = Math.floor((cy - R) / cs) * cs;
      for (let j = 0; j < N; j++) {
        for (let i = 0; i < N; i++) {
          const px = gx + i * cs;
          const py = gy + j * cs;
          const dx = px - cx;
          const dy = py - cy;
          V[j * N + i] = fld(px, py) + Math.exp(-(dx * dx + dy * dy) / 14450);
        }
      }
      const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
      g.addColorStop(0, rg(0.26 * a));
      g.addColorStop(0.6, rg(0.12 * a));
      g.addColorStop(1, rg(0));
      ctx.strokeStyle = g;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let l = 0; l < LV.length; l++) {
        const L = LV[l];
        for (let j = 0; j < N - 1; j++) {
          for (let i = 0; i < N - 1; i++) {
            const a0 = V[j * N + i];
            const b0 = V[j * N + i + 1];
            const c0 = V[(j + 1) * N + i + 1];
            const d0 = V[(j + 1) * N + i];
            const id =
              (a0 > L ? 8 : 0) |
              (b0 > L ? 4 : 0) |
              (c0 > L ? 2 : 0) |
              (d0 > L ? 1 : 0);
            if (id === 0 || id === 15) continue;
            const X = gx + i * cs;
            const Y = gy + j * cs;
            const tX = X + (cs * (L - a0)) / (b0 - a0);
            const rY = Y + (cs * (L - b0)) / (c0 - b0);
            const bX = X + (cs * (L - d0)) / (c0 - d0);
            const lY = Y + (cs * (L - a0)) / (d0 - a0);
            switch (id) {
              case 1:
              case 14:
                ctx.moveTo(X, lY);
                ctx.lineTo(bX, Y + cs);
                break;
              case 2:
              case 13:
                ctx.moveTo(bX, Y + cs);
                ctx.lineTo(X + cs, rY);
                break;
              case 3:
              case 12:
                ctx.moveTo(X, lY);
                ctx.lineTo(X + cs, rY);
                break;
              case 4:
              case 11:
                ctx.moveTo(tX, Y);
                ctx.lineTo(X + cs, rY);
                break;
              case 6:
              case 9:
                ctx.moveTo(tX, Y);
                ctx.lineTo(bX, Y + cs);
                break;
              case 7:
              case 8:
                ctx.moveTo(tX, Y);
                ctx.lineTo(X, lY);
                break;
              case 5:
                ctx.moveTo(tX, Y);
                ctx.lineTo(X, lY);
                ctx.moveTo(bX, Y + cs);
                ctx.lineTo(X + cs, rY);
                break;
              case 10:
                ctx.moveTo(tX, Y);
                ctx.lineTo(X + cs, rY);
                ctx.moveTo(X, lY);
                ctx.lineTo(bX, Y + cs);
                break;
            }
          }
        }
      }
      ctx.stroke();
    };

    const rgs: { x: number; y: number; t: number }[] = [];
    let lastRg = 0;
    const rings = (a: number) => {
      if (a > 0.15 && T - lastRg > 650) {
        rgs.push({ x: cx, y: cy, t: 0 });
        lastRg = T;
        if (rgs.length > 8) rgs.shift();
      }
      for (let i = rgs.length - 1; i >= 0; i--) {
        const r = rgs[i];
        r.t += dt;
        const k = r.t / 2600;
        if (k >= 1) {
          rgs.splice(i, 1);
          continue;
        }
        const rad = 10 + (1 - Math.pow(1 - k, 2)) * 170;
        const al = (1 - k) * 0.3;
        ctx.setLineDash([2, 5]);
        ctx.strokeStyle = rg(al * a);
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(r.x, r.y, rad, 0, TAU);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = rw(al * 1.5 * a);
        for (let m = 0; m < 3; m++) {
          const th = r.t * 0.0004 + m * 2.094;
          ctx.beginPath();
          ctx.arc(
            r.x + Math.cos(th) * rad,
            r.y + Math.sin(th) * rad,
            1.6,
            0,
            TAU
          );
          ctx.fill();
        }
      }
    };

    const FN: Record<Fx, (a: number) => void> = { contour, rings };

    const GROUPS = [
      { s: '[data-cursor="card"]', R: 300, m: 0 },
      { s: GLOW_SELECTOR, R: 210, m: 1 },
    ].map((g) => ({
      ...g,
      o: Array.from(document.querySelectorAll(g.s)).map((el) => ({
        el: el as HTMLElement,
        n: 0,
        w: 0,
        r: null as DOMRect | null,
      })),
    }));

    const pass = (on: boolean, f: number) => {
      const e2 = 1 - Math.pow(1 - 0.18, f);
      for (let gi = 0; gi < GROUPS.length; gi++) {
        const g = GROUPS[gi];
        for (let i = 0; i < g.o.length; i++) {
          const o = g.o[i];
          o.r =
            on || o.n > 0.003 || o.w > 0
              ? o.el.getBoundingClientRect()
              : null;
        }
      }
      maxN = 0;
      for (let gi = 0; gi < GROUPS.length; gi++) {
        const g = GROUPS[gi];
        for (let i = 0; i < g.o.length; i++) {
          const o = g.o[i];
          const r = o.r;
          if (!r) continue;
          const far = r.bottom < -420 || r.top > H + 420;
          let t = 0;
          if (on && !far) {
            const dx = Math.max(r.left - cx, 0, cx - r.right);
            const dy = Math.max(r.top - cy, 0, cy - r.bottom);
            t = Math.max(0, 1 - Math.hypot(dx, dy) / g.R);
          }
          o.n += (t - o.n) * e2;
          if (t === 0 && o.n < 0.002) o.n = 0;
          if (o.n > maxN) maxN = o.n;
          const s = sm(Math.min(1, o.n));
          if (g.m === 0) {
            if (s > 0.004) {
              o.el.style.setProperty("--lx", (cx - r.left).toFixed(1) + "px");
              o.el.style.setProperty("--ly", (cy - r.top).toFixed(1) + "px");
              o.el.style.setProperty("--lo", s.toFixed(3));
              o.w = s;
            } else if (o.w > 0) {
              o.el.style.setProperty("--lo", "0");
              o.w = 0;
            }
          } else if (Math.abs(s - o.w) > 0.004 || (s === 0 && o.w !== 0)) {
            o.el.style.setProperty("--near", s.toFixed(3));
            o.w = s;
          }
        }
      }
    };

    const kick = () => {
      if (!run) {
        run = true;
        last = performance.now();
        requestAnimationFrame(fr);
      }
    };

    const fr = (t: number) => {
      dt = Math.min(t - last, 50);
      last = t;
      T = t;
      const f = dt / 16.67;
      pvx = cx;
      pvy = cy;
      const e1 = 1 - Math.pow(1 - 0.2, f);
      cx += (tx - cx) * e1;
      cy += (ty - cy) * e1;
      vis += (target - vis) * (1 - Math.pow(1 - 0.08, f));
      const on = target === 1;
      const tg: Record<Fx, number> = { contour: 0, rings: 0 };
      if (on || vis > 0.01) {
        for (let i = 0; i < Z.length; i++) {
          const r = Z[i].el.getBoundingClientRect();
          const m = Math.min(cy - r.top, r.bottom - cy);
          tg[Z[i].k] += Math.max(0, Math.min(1, (m + FE) / (2 * FE)));
        }
      }
      const ez = 1 - Math.pow(1 - 0.1, f);
      for (const q of FX_KEYS) {
        WT[q] += (Math.min(1, tg[q]) - WT[q]) * ez;
      }
      pass(on, f);
      ctx.clearRect(0, 0, W, H);
      const al = vis * GA;
      for (const q of FX_KEYS) {
        const w = WT[q] * al;
        if (w > 0.012) {
          FN[q](w);
        } else {
          if (q === "rings" && rgs.length) rgs.length = 0;
        }
      }
      if (on || vis > 0.004 || maxN > 0.004) {
        requestAnimationFrame(fr);
      } else {
        ctx.clearRect(0, 0, W, H);
        run = false;
      }
    };

    const onPointerMove = (e: PointerEvent) => {
      if (e.pointerType && e.pointerType !== "mouse") return;
      tx = e.clientX;
      ty = e.clientY;
      target = 1;
      if (!seen) {
        cx = tx;
        cy = ty;
        pvx = cx;
        pvy = cy;
        seen = true;
      }
      kick();
    };
    const onLeave = () => {
      target = 0;
      seen = false;
      kick();
    };

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    document.documentElement.addEventListener("mouseleave", onLeave);
    window.addEventListener("blur", onLeave);

    return () => {
      window.removeEventListener("resize", rs);
      window.removeEventListener("pointermove", onPointerMove);
      document.documentElement.removeEventListener("mouseleave", onLeave);
      window.removeEventListener("blur", onLeave);
      cv.remove();
    };
  }, []);

  return null;
}
