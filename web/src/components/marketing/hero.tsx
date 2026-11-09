"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

const COMMAND = "femuralabs ml infer --ct scan.nii";

export function Hero() {
  const [typed, setTyped] = useState("");
  const [showOutputs, setShowOutputs] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);

  // Typewriter
  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setTyped(COMMAND);
      setShowOutputs(true);
      return;
    }
    let i = 0;
    let cancelled = false;
    const tick = () => {
      if (cancelled) return;
      setTyped(COMMAND.slice(0, i));
      i += 1;
      if (i <= COMMAND.length) {
        setTimeout(tick, 70 + Math.random() * 45);
      } else {
        setTimeout(() => setShowOutputs(true), 500);
      }
    };
    setTimeout(tick, 700);
    return () => {
      cancelled = true;
    };
  }, []);

  // Cursor-tracking radial glow (matches reference .hero:before with --mx/--my)
  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

    let raf = 0;
    const onMove = (e: PointerEvent) => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        const r = el.getBoundingClientRect();
        el.style.setProperty("--mx", `${e.clientX - r.left}px`);
        el.style.setProperty("--my", `${e.clientY - r.top}px`);
        raf = 0;
      });
    };
    el.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      el.removeEventListener("pointermove", onMove);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      id="hero"
      className="relative overflow-hidden px-4 pt-24 pb-14 text-center sm:flex sm:min-h-[100svh] sm:items-center sm:px-6 sm:pt-[120px] sm:pb-20"
    >
      {/* Ambient radial — reference .hero:after */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-[-20%] h-[560px] w-[900px] -translate-x-1/2 bg-[radial-gradient(closest-side,rgba(77,163,255,0.16),transparent)]"
      />
      {/* Cursor-tracking radial — reference .hero:before */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(520px circle at var(--mx, 50%) var(--my, 35%), rgba(77, 163, 255, 0.09), transparent 70%)",
        }}
      />
      <div className="relative mx-auto w-full max-w-7xl">
        <h1 className="mx-auto max-w-[12ch] text-[clamp(2.2rem,7.6vw,6.6rem)] font-medium leading-none tracking-[-0.065em]">
          Lower-limb CT, measured automatically.
        </h1>
        <p className="mx-auto mt-[22px] max-w-[36ch] text-[clamp(0.95rem,1.4vw,1.2rem)] text-mut">
          Segmentation, meshes and alignment angles from one command.
        </p>
        <div className="mt-[30px] flex flex-col justify-center gap-3 sm:flex-row">
          <Button href="/docs">Read the Docs</Button>
          <Button
            href="https://github.com/sashminea/FemuraLabs"
            variant="ghost"
            external
          >
            Get Started
          </Button>
          <Button href="/simulator" variant="ghost">
            Try the simulator
          </Button>
        </div>

        {/* Terminal — reference dimensions: 560px, 96px, 14px */}
        <div
          data-cursor="card"
          className="mx-auto mt-10 max-w-[560px] overflow-hidden rounded-2xl border border-line bg-[rgba(7,8,9,0.8)] text-left backdrop-blur-md sm:mt-16"
        >
          <div className="flex gap-1.5 border-b border-line px-3.5 py-3">
            <span className="h-[9px] w-[9px] rounded-full bg-white/[0.12]" />
            <span className="h-[9px] w-[9px] rounded-full bg-white/[0.12]" />
            <span className="h-[9px] w-[9px] rounded-full bg-white/[0.12]" />
          </div>
          <div className="min-h-[96px] whitespace-pre px-5 py-[18px] font-mono text-[14px] leading-[1.7]">
            <span className="text-green">$ </span>
            {typed}
            {!showOutputs && (
              <span className="inline-block animate-[blink_1.2s_step-end_infinite]">
                █
              </span>
            )}
            {showOutputs && (
              <>
                {"\n"}
                <span className="text-dim">✓ femur · tibia · fibula · talus</span>
                {"\n"}
                <span className="text-dim">✓ combined_seg.nii written</span>
                {"\n"}
                <span className="text-green">$ </span>
                <span className="inline-block animate-[blink_1.2s_step-end_infinite]">
                  █
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
