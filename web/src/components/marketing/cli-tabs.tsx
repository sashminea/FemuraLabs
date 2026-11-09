"use client";

import { useEffect, useRef, useState } from "react";

import { Reveal } from "@/components/ui/reveal";

const TABS = ["Infer", "Docker", "Train", "Verify"] as const;

type Line = { prompt: boolean; text: string };

const PANES: Line[][] = [
  [
    { prompt: true, text: "femuralabs ml download-weights" },
    { prompt: true, text: "femuralabs ml infer --ct scan.nii --out combined_seg.nii" },
    { prompt: true, text: "femuralabs pipeline run --case combined_seg.nii \\" },
    { prompt: false, text: "  --out output/case01 --angles --fill" },
  ],
  [
    { prompt: true, text: "docker build -t femuralabs-tool ." },
    { prompt: true, text: "docker run --rm femuralabs-tool --help" },
  ],
  [
    { prompt: true, text: "femuralabs ml prepare --out-dir data/ml_npy" },
    { prompt: true, text: "femuralabs ml train --data-dir data/ml_npy \\" },
    { prompt: false, text: "  --out-dir runs/run1 --patch 96 --batch-size 2 --epochs 200" },
    { prompt: true, text: "femuralabs ml validate --checkpoint runs/run1/best.pt \\" },
    { prompt: false, text: "  --data-dir data/ml_npy --val-cases case07,case08" },
  ],
  [
    { prompt: true, text: "pip install -r requirements.txt && pip install -e ." },
    { prompt: true, text: "femuralabs doctor check" },
    { prompt: true, text: "pytest -q" },
    { prompt: true, text: "femuralabs pipeline batch && femuralabs pipeline report" },
  ],
];

const DURATION_MS = 7000;

export function CliTabs() {
  const [active, setActive] = useState(0);
  const [progress, setProgress] = useState(0);
  const [paused, setPaused] = useState(false);
  const elapsedRef = useRef(0);
  const rafRef = useRef(0);

  const selectTab = (i: number) => {
    setActive(i);
    elapsedRef.current = 0;
    setProgress(0);
  };

  useEffect(() => {
    if (paused) return;
    if (typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let last = performance.now();
    let cancelled = false;

    const tick = (now: number) => {
      if (cancelled) return;
      const dt = Math.min(now - last, 100);
      last = now;
      elapsedRef.current += dt;
      if (elapsedRef.current >= DURATION_MS) {
        elapsedRef.current = 0;
        setActive((a) => (a + 1) % TABS.length);
        setProgress(0);
      } else {
        setProgress(elapsedRef.current / DURATION_MS);
      }
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      cancelled = true;
      cancelAnimationFrame(rafRef.current);
    };
  }, [paused]);

  return (
    <section id="cli" className="py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <h2 className="max-w-[12ch] text-[clamp(2rem,4.8vw,3.8rem)] font-medium leading-[1.04] tracking-[-0.055em]">
            Install, run, reproduce.
          </h2>
        </Reveal>

        <Reveal delay={80}>
          <div className="mt-14 grid items-start gap-8 md:grid-cols-[.8fr_1.4fr]">
            <div className="flex flex-col">
              {TABS.map((t, i) => {
                const isActive = active === i;
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => selectTab(i)}
                    role="tab"
                    aria-selected={isActive}
                    className={`relative border-t border-line py-5 text-left text-[clamp(1.3rem,2.4vw,2rem)] font-medium leading-tight tracking-[-0.04em] transition-[color,padding] duration-300 ${
                      isActive ? "pl-3.5 text-tx" : "text-dim hover:text-mut"
                    }`}
                  >
                    {t}
                    {isActive && (
                      <span
                        aria-hidden
                        className="absolute -bottom-px left-0 h-px w-full origin-left bg-blue"
                        style={{ transform: `scaleX(${progress})` }}
                      />
                    )}
                  </button>
                );
              })}
            </div>

            <div
              data-cursor="card"
              onMouseEnter={() => setPaused(true)}
              onMouseLeave={() => setPaused(false)}
              className="overflow-hidden rounded-2xl border border-line bg-[rgba(7,8,9,0.8)]"
            >
              <div className="flex gap-1.5 border-b border-line px-3.5 py-3">
                <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
              </div>
              <pre className="min-h-[200px] overflow-x-auto px-3 py-4 font-mono text-[11.5px] leading-[1.7] text-tx sm:px-5 sm:py-5 sm:text-[13.5px]">
                {PANES[active].map((line, i) => (
                  <div key={i} className="whitespace-pre">
                    {line.prompt && <span className="text-green">$ </span>}
                    {line.text}
                  </div>
                ))}
              </pre>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
