"use client";

import { useEffect, useRef, useState } from "react";
import Term from "./Term";
import { DISPLAY_ITEMS } from "./glossary";
import type { DisplayKind, GlossaryKey } from "./glossary";
import { fmt } from "@/lib/format";

export type Target = "neutral" | "valgus3" | "valgus6";
export type Status = "under" | "target" | "over";

export const THETA_MAX = 15;
/** Degrees of valgus each target aims for, measured from neutral. */
export const TARGET_OFFSET: Record<Target, number> = { neutral: 0, valgus3: 3, valgus6: 6 };

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

// ============ Shared bits ============

export function PanelTitle({ children, right }: { children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="mb-4 flex min-h-6 items-center justify-between">
      <h2 className="m-0 text-[13px] font-medium tracking-[-.01em] text-tx">{children}</h2>
      {right}
    </div>
  );
}

export function Segmented<V extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: { value: V; label: string }[];
  value: V;
  onChange: (v: V) => void;
  label: string;
}) {
  return (
    <div className="sim-seg" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} aria-pressed={value === o.value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

// ============ Case info ============

export function CaseInfo({
  caseName,
  side,
  preHka,
  preMpta,
  widthMm,
}: {
  caseName: string;
  side: "R" | "L";
  preHka: number;
  preMpta: number;
  widthMm: number;
}) {
  const rows: { term: GlossaryKey; label: string; value: string }[] = [
    { term: "hka", label: "Pre-op HKA", value: `${fmt(preHka, 2, true)}°` },
    { term: "mpta", label: "Pre-op MPTA", value: `${fmt(preMpta)}°` },
    { term: "plateauWidth", label: "Plateau width", value: `${widthMm.toFixed(1)} mm` },
    { term: "cutPlane", label: "Cut plane", value: "15 mm" },
  ];
  return (
    <div className="rounded-xl border border-line bg-white/[0.03] p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="text-[11px] font-medium uppercase tracking-[.08em] text-dim">Case</span>
        <span className="rounded-full border border-line px-2 py-0.5 text-[11px] text-mut">
          {side === "R" ? "Right" : "Left"} tibia
        </span>
      </div>
      <div className="mt-2 truncate text-[15px] font-medium tracking-[-.01em] text-tx" title={caseName}>
        {caseName}
      </div>
      <dl className="m-0 mt-4 grid grid-cols-[1fr_auto] gap-x-4 gap-y-2.5 border-t border-line pt-4 text-[12.5px]">
        {rows.map((r) => (
          <div key={r.label} className="contents">
            <dt className="text-mut">
              <Term term={r.term} plain>
                {r.label}
              </Term>
            </dt>
            <dd className="num m-0 text-right text-tx">{r.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

// ============ Correction ============

const TARGET_OPTIONS: { value: Target; label: string }[] = [
  { value: "neutral", label: "Neutral" },
  { value: "valgus3", label: "Valgus 3°" },
  { value: "valgus6", label: "Valgus 6°" },
];

export function CorrectionControl({
  theta,
  setTheta,
  target,
  onTarget,
  band,
  title = true,
}: {
  theta: number;
  setTheta: (v: number) => void;
  target: Target;
  /** Picks a target and moves θ to the angle that reaches it. */
  onTarget: (t: Target) => void;
  /** θ range (degrees) that lands inside the target band, or null if unreachable. */
  band: [number, number] | null;
  title?: boolean;
}) {
  const [text, setText] = useState(theta.toFixed(1));
  const editing = useRef(false);

  useEffect(() => {
    if (!editing.current) setText(theta.toFixed(1));
  }, [theta]);

  // Slider geometry: the 16px thumb travels between 8px and (width − 8px).
  const at = (deg: number) => `calc(8px + (100% - 16px) * ${deg / THETA_MAX})`;
  const span = (a: number, b: number) => `calc((100% - 16px) * ${(b - a) / THETA_MAX})`;
  const bandCenter = band ? (band[0] + band[1]) / 2 : 0;

  return (
    <div>
      {title && <PanelTitle>Correction</PanelTitle>}

      <div className="flex items-center justify-between">
        <label htmlFor="sim-theta" className="text-xs text-mut">
          <Term term="correctionAngle">Angle θ</Term>
        </label>
        <div className="sim-field">
          <input
            id="sim-theta"
            className="num"
            type="number"
            min={0}
            max={THETA_MAX}
            step={0.1}
            value={text}
            onFocus={() => (editing.current = true)}
            onChange={(e) => {
              setText(e.target.value);
              const v = parseFloat(e.target.value);
              if (!isNaN(v)) setTheta(clamp(v, 0, THETA_MAX));
            }}
            onBlur={() => {
              editing.current = false;
              setText(theta.toFixed(1));
            }}
          />
          <span>°</span>
        </div>
      </div>

      <div className="relative mt-3.5 h-5">
        <div aria-hidden className="absolute left-2 right-2 top-2 h-1 rounded-sm bg-white/10" />
        {band && (
          <div
            aria-hidden
            className="absolute top-[7px] h-1.5 rounded-[3px] bg-green/55"
            style={{ left: at(band[0]), width: `max(6px, ${span(band[0], band[1])})` }}
          />
        )}
        <div
          aria-hidden
          className="absolute left-2 top-2 h-1 rounded-sm bg-blue"
          style={{ width: span(0, theta) }}
        />
        <input
          className="sim-range"
          type="range"
          min={0}
          max={THETA_MAX}
          step={0.5}
          value={theta}
          onChange={(e) => setTheta(parseFloat(e.target.value))}
          aria-label="Correction angle"
        />
      </div>

      <div className="num relative mt-1 h-4 text-[11px] text-dim">
        <span className="absolute left-0">0°</span>
        {band && (
          <span
            className="absolute -translate-x-1/2 whitespace-nowrap text-green"
            style={{ left: `clamp(16%, ${at(bandCenter)}, 84%)` }}
          >
            <Term term="targetRange" plain>
              Target zone
            </Term>
          </span>
        )}
        <span className="absolute right-0">{THETA_MAX}°</span>
      </div>

      <div className="mb-2 mt-5 text-xs text-mut">
        <Term term="targetValgus">Target</Term>
      </div>
      <Segmented options={TARGET_OPTIONS} value={target} onChange={onTarget} label="Target alignment" />
    </div>
  );
}

// ============ Results ============

function StatusPill({ status }: { status: Status }) {
  const ok = status === "target";
  const text = ok ? "In target range" : status === "under" ? "Under-corrected" : "Over-corrected";
  return (
    <div
      role="status"
      className={`inline-flex h-6 items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 text-xs font-medium ${
        ok
          ? "border-green/40 bg-green/10 text-green"
          : "border-amber/40 bg-amber/10 text-amber"
      }`}
    >
      <span className={`size-1.5 rounded-full ${ok ? "bg-green" : "bg-amber"}`} />
      {text}
    </div>
  );
}

type StatProps = {
  term: GlossaryKey;
  label: string;
  value: string;
  unit: string;
  sub: string;
};

/** Desktop: one roomy row per measurement, label and context left, value right. */
function StatRow({ term, label, value, unit, sub }: StatProps) {
  return (
    <div className="flex items-center justify-between gap-4 py-4">
      <div className="min-w-0">
        <div className="text-[13px] text-mut">
          <Term term={term}>{label}</Term>
        </div>
        <div className="num mt-1.5 text-xs text-dim">{sub}</div>
      </div>
      <div className="num whitespace-nowrap text-[28px] font-medium leading-none tracking-[-.04em] text-tx">
        {value}
        <span className="ml-1 text-base font-normal tracking-normal text-mut">{unit}</span>
      </div>
    </div>
  );
}

/** Mobile: three columns, with real padding and wrapping context text. */
function StatCell({ term, label, value, unit, sub }: StatProps) {
  return (
    <div className="min-w-0 border-l border-line px-4 py-4 first:border-l-0">
      <div className="text-xs text-mut">
        <Term term={term}>{label}</Term>
      </div>
      <div className="num mt-3 whitespace-nowrap text-xl font-medium leading-none tracking-[-.04em] text-tx">
        {value}
        <span className="ml-0.5 text-[11px] font-normal tracking-normal text-mut">{unit}</span>
      </div>
      <div className="num mt-2.5 text-[11px] leading-snug text-dim">{sub}</div>
    </div>
  );
}

export function Results({
  gap,
  mpta,
  hka,
  preMpta,
  preHka,
  widthMm,
  status,
  tMin,
  tMax,
  compact,
}: {
  gap: number;
  mpta: number;
  hka: number;
  preMpta: number;
  preHka: number;
  widthMm: number;
  status: Status;
  tMin: number;
  tMax: number;
  compact?: boolean;
}) {
  const stats: StatProps[] = [
    {
      term: "wedgeGap",
      label: "Wedge gap",
      value: fmt(gap),
      unit: "mm",
      sub: compact ? `on ${widthMm.toFixed(1)} mm` : `on ${widthMm.toFixed(1)} mm plateau`,
    },
    { term: "mpta", label: "MPTA", value: fmt(mpta), unit: "°", sub: `was ${fmt(preMpta)}°` },
    { term: "hka", label: "HKA", value: fmt(hka, 2, true), unit: "°", sub: `was ${fmt(preHka, 2, true)}°` },
  ];

  if (compact) {
    return (
      <div>
        <div className="flex justify-end px-4 pt-3">
          <StatusPill status={status} />
        </div>
        <div className="mt-3 grid grid-cols-3 border-y border-line">
          {stats.map((s) => (
            <StatCell key={s.label} {...s} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PanelTitle right={<StatusPill status={status} />}>Results</PanelTitle>
      <div className="divide-y divide-line border-y border-line">
        {stats.map((s) => (
          <StatRow key={s.label} {...s} />
        ))}
      </div>
      <div className="num mt-4 text-xs text-dim">
        <Term term="targetRange" plain>
          Target HKA
        </Term>{" "}
        {fmt(tMin, 0)}° to {fmt(tMax, 0, true)}°
      </div>
    </div>
  );
}

// ============ Layers ============

function EyeIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="shrink-0"
      aria-hidden
    >
      {open ? (
        <>
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </>
      ) : (
        <>
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
          <line x1="1" y1="1" x2="23" y2="23" />
        </>
      )}
    </svg>
  );
}

function Swatch({ color, kind, on }: { color: string; kind: DisplayKind; on: boolean }) {
  const wrap = `inline-flex h-3 w-4 shrink-0 items-center justify-center transition-opacity ${
    on ? "opacity-100" : "opacity-35"
  }`;
  if (kind === "bone") {
    return (
      <span className={wrap}>
        <span className="size-[9px] rounded-full" style={{ background: color }} />
      </span>
    );
  }
  if (kind === "solid") {
    return (
      <span className={wrap}>
        <span className="h-0.5 w-3.5 rounded-[1px]" style={{ background: color }} />
      </span>
    );
  }
  if (kind === "dashed") {
    return (
      <span className={wrap}>
        <span
          className="h-0.5 w-3.5"
          style={{ background: `repeating-linear-gradient(90deg, ${color} 0 3px, transparent 3px 6px)` }}
        />
      </span>
    );
  }
  if (kind === "arc") {
    return (
      <span className={wrap}>
        <span
          className="mt-[3px] h-[7px] w-3 rounded-t-[12px]"
          style={{ borderTop: `2px solid ${color}` }}
        />
      </span>
    );
  }
  if (kind === "wedge") {
    return (
      <span className={wrap}>
        <span
          style={{
            width: 0,
            height: 0,
            borderLeft: "5px solid transparent",
            borderRight: "5px solid transparent",
            borderBottom: `9px solid ${color}`,
            opacity: 0.9,
          }}
        />
      </span>
    );
  }
  return (
    <span className={`${wrap} gap-px`}>
      <span className="size-[3px] rounded-full bg-blue" />
      <span className="size-[3px] rounded-full bg-[#ffaa55]" />
      <span className="size-[3px] rounded-full bg-blue" />
      <span className="size-[3px] rounded-full bg-green" />
    </span>
  );
}

const GROUPS = ["Bones", "Axes", "Angles", "Markers"];

export function Layers({
  visible,
  setVisible,
  opacity,
  setOpacity,
  title = true,
}: {
  visible: Record<string, boolean>;
  setVisible: (fn: (v: Record<string, boolean>) => Record<string, boolean>) => void;
  opacity: number;
  setOpacity: (v: number) => void;
  title?: boolean;
}) {
  return (
    <div>
      {title && <PanelTitle>Layers</PanelTitle>}
      {GROUPS.map((grp, gi) => {
        const items = DISPLAY_ITEMS.filter((i) => i.group === grp);
        if (!items.length) return null;
        return (
          <div key={grp} className={gi === 0 ? "" : "mt-4"}>
            <div className="mb-1 text-xs text-dim">{grp}</div>
            {items.map((item) => {
              const on = visible[item.key] !== false;
              return (
                <button
                  key={item.key}
                  className="sim-row"
                  aria-pressed={on}
                  onClick={() => setVisible((v) => ({ ...v, [item.key]: !on }))}
                >
                  <Swatch color={item.color} kind={item.kind} on={on} />
                  <span className="min-w-0 flex-1">
                    <Term term={item.key as GlossaryKey} plain hoverOnly>
                      {item.label}
                    </Term>
                  </span>
                  <span className={`inline-flex ${on ? "text-mut" : "text-dim"}`}>
                    <EyeIcon open={on} />
                  </span>
                </button>
              );
            })}
            {grp === "Bones" && (
              <div className="mt-2.5">
                <div className="flex justify-between text-xs text-mut">
                  <label htmlFor="sim-opacity" title="Lower it to see axes, arcs and the wedge through the bones">
                    Opacity
                  </label>
                  <span className="num">{Math.round(opacity * 100)}%</span>
                </div>
                <div className="relative mt-1.5 h-5">
                  <div aria-hidden className="absolute left-2 right-2 top-2 h-1 rounded-sm bg-white/10" />
                  <div
                    aria-hidden
                    className="absolute left-2 top-2 h-1 rounded-sm bg-blue"
                    style={{ width: `calc((100% - 16px) * ${(opacity - 0.1) / 0.9})` }}
                  />
                  <input
                    id="sim-opacity"
                    className="sim-range"
                    type="range"
                    min={0.1}
                    max={1}
                    step={0.05}
                    value={opacity}
                    onChange={(e) => setOpacity(parseFloat(e.target.value))}
                    aria-label="Bone opacity"
                  />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}