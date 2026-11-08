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
        setTimeout(tick, 45 + Math.random() * 50);
      } else {
        setTimeout(() => setShowOutputs(true), 400);
      }
    };
    setTimeout(tick, 700);
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="relative overflow-hidden px-6 pt-32 pb-20">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(520px_circle_at_50%_35%,rgba(77,163,255,0.09),transparent_70%)]"
      />
      <div className="relative mx-auto max-w-7xl text-center">
        <h1 className="mx-auto max-w-[12ch] text-[clamp(2.6rem,7.6vw,6.6rem)] font-medium leading-none tracking-[-0.065em]">
          Lower-limb CT, measured automatically.
        </h1>
        <p className="mx-auto mt-6 max-w-[36ch] text-[clamp(1rem,1.4vw,1.2rem)] text-mut">
          Segmentation, meshes and alignment angles from one command.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button href="/docs">Read the Docs</Button>
          <Button href="https://github.com/sashminea/FemuraLabs" variant="ghost" external>
            Get Started
          </Button>
        </div>

        <div className="mx-auto mt-14 max-w-lg overflow-hidden rounded-2xl border border-line bg-[rgba(7,8,9,0.8)] text-left backdrop-blur-md">
          <div className="flex gap-1.5 border-b border-line px-3.5 py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
          </div>
          <div className="min-h-[96px] whitespace-pre px-5 py-4 font-mono text-sm leading-relaxed">
            <span className="text-green">$ </span>
            {typed}
            <span className="inline-block animate-[blink_1s_step-end_infinite]">█</span>
            {showOutputs && (
              <>
                {"\n"}
                <span className="text-dim">✓ femur · tibia · fibula · talus</span>
                {"\n"}
                <span className="text-dim">✓ combined_seg.nii written</span>
                {"\n"}
                <span className="text-green">$ </span>
                <span className="inline-block animate-[blink_1s_step-end_infinite]">█</span>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
