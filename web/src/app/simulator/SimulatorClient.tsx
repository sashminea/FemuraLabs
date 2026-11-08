"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import SimulatorScene from "./SimulatorScene";
import Explainer from "./Explainer";
import {
  CaseInfo,
  CorrectionControl,
  Layers,
  Results,
  Segmented,
  TARGET_OFFSET,
  THETA_MAX,
} from "./Panels";
import type { Target } from "./Panels";
import { wedgeGap, newMPTA, newHKA, correctionStatus } from "@/lib/osteotomy";
import { DISPLAY_ITEMS } from "./glossary";

type Config = {
  case: string;
  side: "R" | "L";
  hip_local: [number, number, number];
  ankle_local: [number, number, number];
  hinge_local: [number, number, number];
  medial_edge_local: [number, number, number];
  plateau_medial_local: [number, number, number];
  plateau_lateral_local: [number, number, number];
  cut_plane_z_local: number;
  tibia_width_at_cut_mm: number;
  pre_hka_deg: number;
  pre_mpta_deg: number;
};

type MobileTab = "correction" | "explain" | "layers" | "case";

const RANGES: Record<Target, [number, number]> = {
  neutral: [-1, 1],
  valgus3: [-4, -2],
  valgus6: [-7, -5],
};
const DEFAULT_VISIBILITY = Object.fromEntries(DISPLAY_ITEMS.map((i) => [i.key, true]));

const LEFT_DEFAULT = 304;
const LEFT_MIN = 264;
const LEFT_MAX = 400;
const RIGHT_DEFAULT = 400;
const RIGHT_MIN = 340;
const RIGHT_MAX = 520;
const LS_LEFT = "sim.leftWidth.v5";
const LS_RIGHT = "sim.rightWidth.v5";

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

function DragHandle({
  onStart,
  onReset,
}: {
  onStart: (e: React.PointerEvent) => void;
  onReset: () => void;
}) {
  return (
    <div className="sim-drag">
      <div
        onPointerDown={onStart}
        onDoubleClick={onReset}
        title="Drag to resize, double-click to reset"
        className="absolute inset-y-0 -left-1 w-[9px] cursor-col-resize select-none"
        style={{ touchAction: "none" }}
      />
    </div>
  );
}

function Brand({ subtitle = true }: { subtitle?: boolean }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <Link href="/" className="text-[17px] font-medium tracking-tight text-tx">
          FemuraLabs
        </Link>
        <Link href="/" className="sim-link inline-flex items-center gap-1">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M15 6l-6 6 6 6" />
          </svg>
          Site
        </Link>
      </div>
      {subtitle && <p className="mt-1 text-xs text-dim">Osteotomy wedge simulator</p>}
    </div>
  );
}

const SHELL = "sim fixed inset-0 z-[100] flex bg-bg font-sans text-tx";

export default function SimulatorClient() {
  const [config, setConfig] = useState<Config | null>(null);
  const [failed, setFailed] = useState(false);
  const [theta, setTheta] = useState(8);
  const [target, setTarget] = useState<Target>("neutral");
  const [opacity, setOpacity] = useState(0.85);
  const [visible, setVisible] = useState<Record<string, boolean>>(DEFAULT_VISIBILITY);
  const [isMobile, setIsMobile] = useState(false);
  const [leftW, setLeftW] = useState(LEFT_DEFAULT);
  const [rightW, setRightW] = useState(RIGHT_DEFAULT);
  const [tab, setTab] = useState<MobileTab>("correction");

  // Fetch config.
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
    fetch(`${base}/simulator/config.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setConfig)
      .catch((err) => {
        console.error("[simulator] config fetch failed", err);
        setFailed(true);
      });
  }, []);

  // Mobile breakpoint.
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 1024px)");
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  // The simulator owns the whole viewport, so stop the page behind it from scrolling.
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  // Persist panel widths.
  useEffect(() => {
    const l = localStorage.getItem(LS_LEFT);
    const r = localStorage.getItem(LS_RIGHT);
    if (l) {
      const v = parseInt(l, 10);
      if (!isNaN(v)) setLeftW(clamp(v, LEFT_MIN, LEFT_MAX));
    }
    if (r) {
      const v = parseInt(r, 10);
      if (!isNaN(v)) setRightW(clamp(v, RIGHT_MIN, RIGHT_MAX));
    }
  }, []);
  useEffect(() => {
    localStorage.setItem(LS_LEFT, String(leftW));
  }, [leftW]);
  useEffect(() => {
    localStorage.setItem(LS_RIGHT, String(rightW));
  }, [rightW]);

  // Range of θ that lands inside the selected target band. Sampled from the real
  // formulas so it stays correct if lib/osteotomy changes.
  const band = useMemo<[number, number] | null>(() => {
    if (!config) return null;
    const [lo, hi] = RANGES[target];
    let first: number | null = null;
    let last: number | null = null;
    for (let i = 0; i <= THETA_MAX * 10; i++) {
      const t = i / 10;
      if (correctionStatus(newHKA(config.pre_hka_deg, t), lo, hi) === "target") {
        if (first === null) first = t;
        last = t;
      }
    }
    return first === null || last === null ? null : [first, last];
  }, [config, target]);

  if (!config && !failed) {
    return (
      <div className="fixed inset-0 z-[100] grid place-items-center bg-bg font-sans text-sm text-dim">
        Loading simulator…
      </div>
    );
  }

  if (!config) {
    return (
      <div className="fixed inset-0 z-[100] grid place-items-center bg-bg p-6 text-center font-sans text-sm text-amber">
        Couldn’t load the case data. Refresh the page to try again.
      </div>
    );
  }

  const gap = wedgeGap(config.tibia_width_at_cut_mm, theta);
  const mpta = newMPTA(config.pre_mpta_deg, theta);
  const hka = newHKA(config.pre_hka_deg, theta);
  const [tMin, tMax] = RANGES[target];
  const status = correctionStatus(hka, tMin, tMax);

  // Choosing a target also moves θ to the angle that reaches it.
  const selectTarget = (t: Target) => {
    setTarget(t);
    setTheta(clamp(config.pre_hka_deg + TARGET_OFFSET[t], 0, THETA_MAX));
  };

  const makeDragHandler = (side: "left" | "right") => (e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const startX = e.clientX;
    const startW = side === "left" ? leftW : rightW;
    const el = e.currentTarget as HTMLElement;
    el.setPointerCapture(e.pointerId);
    const onMove = (ev: PointerEvent) => {
      const delta = ev.clientX - startX;
      if (side === "left") setLeftW(clamp(startW + delta, LEFT_MIN, LEFT_MAX));
      else setRightW(clamp(startW - delta, RIGHT_MIN, RIGHT_MAX));
    };
    const onUp = (ev: PointerEvent) => {
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerup", onUp);
      try {
        el.releasePointerCapture(ev.pointerId);
      } catch {}
    };
    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerup", onUp);
  };

  const scene = (
    <SimulatorScene theta={theta} side={config.side} config={config} opacity={opacity} visible={visible} />
  );

  const caseInfo = (
    <CaseInfo
      caseName={config.case}
      side={config.side}
      preHka={config.pre_hka_deg}
      preMpta={config.pre_mpta_deg}
      widthMm={config.tibia_width_at_cut_mm}
    />
  );

  const correction = (showTitle: boolean) => (
    <CorrectionControl
      theta={theta}
      setTheta={setTheta}
      target={target}
      onTarget={selectTarget}
      band={band}
      title={showTitle}
    />
  );

  const layers = (showTitle: boolean) => (
    <Layers
      visible={visible}
      setVisible={setVisible}
      opacity={opacity}
      setOpacity={setOpacity}
      title={showTitle}
    />
  );

  const results = (compact: boolean) => (
    <Results
      gap={gap}
      mpta={mpta}
      hka={hka}
      preMpta={config.pre_mpta_deg}
      preHka={config.pre_hka_deg}
      widthMm={config.tibia_width_at_cut_mm}
      status={status}
      tMin={tMin}
      tMax={tMax}
      compact={compact}
    />
  );

  const explainer = (
    <Explainer
      preHka={config.pre_hka_deg}
      preMpta={config.pre_mpta_deg}
      theta={theta}
      gap={gap}
      mpta={mpta}
      hka={hka}
      target={target}
      tMin={tMin}
      tMax={tMax}
      status={status}
      widthMm={config.tibia_width_at_cut_mm}
      caseName={config.case}
      side={config.side}
    />
  );

  // ---------- Mobile ----------
  if (isMobile) {
    return (
      <div data-sim-root className={`${SHELL} flex-col`}>
        <header className="flex h-12 shrink-0 items-center justify-between border-b border-line px-4">
          <Brand subtitle={false} />
        </header>
        <div className="sim-canvas relative h-[40dvh] min-h-[220px] shrink-0">{scene}</div>
        <div className="shrink-0 border-t border-line bg-bg">{results(true)}</div>
        <div className="shrink-0 bg-bg px-3 py-2.5">
          <Segmented<MobileTab>
            label="Panel"
            value={tab}
            onChange={setTab}
            options={[
              { value: "correction", label: "Correction" },
              { value: "explain", label: "Explainer" },
              { value: "layers", label: "Layers" },
              { value: "case", label: "Case" },
            ]}
          />
        </div>
        <div
          className="sim-scroll min-h-0 flex-1 overflow-y-auto bg-bg px-4 pt-2"
          style={{ paddingBottom: "calc(24px + env(safe-area-inset-bottom))" }}
        >
          {tab === "correction" && correction(false)}
          {tab === "explain" && explainer}
          {tab === "layers" && layers(false)}
          {tab === "case" && caseInfo}
        </div>
      </div>
    );
  }

  // ---------- Desktop ----------
  return (
    <div data-sim-root className={SHELL}>
      {/* Left: brand, case, correction, layers */}
      <aside className="sim-scroll shrink-0 overflow-y-auto bg-bg" style={{ width: leftW }}>
        <div className="p-5 pb-4">
          <Brand />
        </div>
        <div className="px-5 pb-5">{caseInfo}</div>
        <div className="border-t border-line p-5">{correction(true)}</div>
        <div className="border-t border-line p-5">{layers(true)}</div>
      </aside>

      <DragHandle onStart={makeDragHandler("left")} onReset={() => setLeftW(LEFT_DEFAULT)} />

      {/* Canvas */}
      <main className="sim-canvas relative min-w-0 flex-1 overflow-hidden">
        {scene}
        <div className="pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full border border-line bg-black/40 px-3 py-1.5 text-xs text-dim backdrop-blur-md">
          Drag to rotate, scroll to zoom
        </div>
      </main>

      <DragHandle onStart={makeDragHandler("right")} onReset={() => setRightW(RIGHT_DEFAULT)} />

      {/* Right: results and explainer */}
      <aside className="flex min-h-0 shrink-0 flex-col bg-bg" style={{ width: rightW }}>
        <div className="shrink-0 p-5">{results(false)}</div>
        <div className="sim-scroll min-h-0 flex-1 overflow-y-auto border-t border-line p-5">{explainer}</div>
      </aside>
    </div>
  );
}