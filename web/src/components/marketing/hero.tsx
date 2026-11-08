"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

const COMMAND = "femuralabs ml infer --ct scan.nii";

export function Hero() {
  const [typed, setTyped] = useState("");
  const [showOutputs, setShowOutputs] = useState(false);

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

  return (
    <section className="relative overflow-hidden px-4 pt-28 pb-16 sm:px-6 sm:pt-32 sm:pb-20">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(560px_circle_at_50%_35%,rgba(77,163,255,0.09),transparent_70%)]"
      />
      <div className="relative mx-auto max-w-7xl text-center">
        <h1 className="mx-auto max-w-[12ch] text-[clamp(2.2rem,7.6vw,6.6rem)] font-medium leading-none tracking-[-0.065em]">
          Lower-limb CT, measured automatically.
        </h1>
        <p className="mx-auto mt-5 max-w-[36ch] text-[clamp(0.95rem,1.4vw,1.2rem)] text-mut sm:mt-6">
          Segmentation, meshes and alignment angles from one command.
        </p>
        <div className="mt-7 flex flex-col justify-center gap-3 sm:mt-8 sm:flex-row">
          <Button href="/docs">Read the Docs</Button>
          <Button href="https://github.com/sashminea/FemuraLabs" variant="ghost" external>
            Get Started
          </Button>
          <Button href="/simulator" variant="ghost">
            Try the simulator
          </Button>
        </div>

        <div className="mx-auto mt-12 max-w-xl overflow-hidden rounded-2xl border border-line bg-[rgba(7,8,9,0.8)] text-left backdrop-blur-md sm:mt-14 sm:max-w-2xl">
          <div className="flex gap-1.5 border-b border-line px-4 py-2.5 sm:px-4 sm:py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
          </div>
          <div className="min-h-[140px] whitespace-pre px-5 py-4 font-mono text-[13px] leading-[1.7] sm:min-h-[160px] sm:px-6 sm:py-5 sm:text-[15px]">
            <span className="text-green">$ </span>
            {typed}
            {!showOutputs && (
              <span className="inline-block animate-[blink_1.2s_step-end_infinite]">█</span>
            )}
            {showOutputs && (
              <>
                {"\n"}
                <span className="text-dim">✓ femur · tibia · fibula · talus</span>
                {"\n"}
                <span className="text-dim">✓ combined_seg.nii written</span>
                {"\n"}
                <span className="text-green">$ </span>
                <span className="inline-block animate-[blink_1.2s_step-end_infinite]">█</span>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
