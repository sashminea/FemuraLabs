import { CountUp } from "@/components/ui/count-up";
import { Reveal } from "@/components/ui/reveal";

export function Bento() {
  return (
    <section id="bento" className="py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <h2 className="max-w-[14ch] text-[clamp(2rem,4.8vw,3.8rem)] font-medium leading-[1.04] tracking-[-0.055em]">
            Built for research that reproduces.
          </h2>
        </Reveal>

        <div className="mt-14 grid gap-4 md:grid-cols-10">
          {/* SegResNet card */}
          <Reveal className="md:col-span-6">
            <div className="flex h-full flex-col rounded-[20px] border border-line bg-[radial-gradient(90%_90%_at_100%_0%,rgba(77,163,255,0.16),transparent_60%),var(--color-s1)] p-6 md:p-9">
              <h3 className="text-[1.3rem] font-medium leading-tight tracking-[-0.03em]">
                A SegResNet written from scratch
              </h3>
              <p className="mt-2 max-w-[42ch] text-[15px] text-mut">
                Validated across a rigorous 4-fold cross-validation on all 8 subjects.
                Every subject was held out exactly once to prove generalisation.
              </p>
              <div className="mt-8 flex items-center gap-3.5 pt-7 text-[clamp(3rem,7vw,6rem)] font-medium leading-none tracking-[-0.07em]">
                <span className="h-2.5 w-2.5 flex-none rounded-full bg-blue animate-[pulse-dot_2s_ease-out_infinite]" />
                <CountUp value={0.922} decimals={3} />
                <span className="text-[0.3em] font-normal tracking-[-0.02em] text-mut">
                  Mean Dice
                </span>
              </div>
              <div className="mt-5 flex flex-wrap gap-x-7 gap-y-2.5 font-mono text-[13px] text-mut">
                <span>Femur<b className="ml-1.5 font-medium text-tx">0.94 ± 0.06</b></span>
                <span>Tibia<b className="ml-1.5 font-medium text-tx">0.91 ± 0.06</b></span>
                <span>Fibula<b className="ml-1.5 font-medium text-tx">0.91 ± 0.04</b></span>
                <span>Talus<b className="ml-1.5 font-medium text-tx">0.92 ± 0.03</b></span>
              </div>
            </div>
          </Reveal>

          {/* Geometric precision card */}
          <Reveal delay={120} className="md:col-span-4">
            <div className="flex h-full flex-col rounded-[20px] border border-line bg-s1 p-6 md:p-9">
              <h3 className="text-[1.3rem] font-medium leading-tight tracking-[-0.03em]">
                Geometric precision
              </h3>
              <p className="mt-2 max-w-[42ch] text-[15px] text-mut">
                Millimetre-level surface accuracy. Passed through the geometric landmark
                pipeline, the predicted masks yield an HKA error of just 0.98°.
              </p>
              <div className="mt-auto flex items-center gap-3.5 pt-6 text-[clamp(2.6rem,5vw,4rem)] font-medium leading-none tracking-[-0.07em]">
                <CountUp value={1.5} decimals={1} />
                <span className="text-[0.35em] font-normal tracking-[-0.02em] text-mut">
                  mm median HD95
                </span>
              </div>
              <div className="mt-4 flex justify-center">
                <svg viewBox="0 0 200 200" className="w-full max-w-[220px]">
                  <g className="animate-[spin-slow_60s_linear_infinite] [animation-play-state:paused] group-hover:[animation-play-state:running]">
                    <path
                      d="M100 20 L90 100 L104 180"
                      fill="none"
                      stroke="rgba(255,255,255,0.35)"
                      strokeWidth="1.5"
                    />
                    <path
                      d="M100 20 L104 180"
                      stroke="#4da3ff"
                      strokeWidth="1.5"
                      strokeDasharray="4 4"
                      fill="none"
                    />
                    <path
                      d="M96 70 Q85 100 96 128"
                      fill="none"
                      stroke="#4da3ff"
                      strokeWidth="1.5"
                    />
                    <circle cx="100" cy="20" r="8" fill="#0a0a0a" stroke="#ecebe6" strokeWidth="1.5" />
                    <circle cx="90" cy="100" r="6" fill="#0a0a0a" stroke="#ecebe6" strokeWidth="1.5" />
                    <circle cx="104" cy="180" r="5" fill="#0a0a0a" stroke="#ecebe6" strokeWidth="1.5" />
                  </g>
                </svg>
              </div>
            </div>
          </Reveal>

          {/* CLI card */}
          <Reveal delay={60} className="md:col-span-4">
            <div className="flex h-full flex-col rounded-[20px] border border-line bg-s1 p-6 md:p-9">
              <h3 className="text-[1.3rem] font-medium leading-tight tracking-[-0.03em]">
                Hours of Slicer work, one command
              </h3>
              <p className="mt-2 max-w-[42ch] text-[15px] text-mut">
                A typed CLI built with Typer and Rich.
              </p>
              <div className="mt-auto pt-5">
                <pre className="overflow-x-auto rounded-xl border border-line bg-[#07080a] p-4 font-mono text-[13px] leading-relaxed">
                  <span className="text-green">$</span> femuralabs pipeline run{"\n"}
                  <span className="text-green">$</span> femuralabs pipeline report
                </pre>
              </div>
            </div>
          </Reveal>

          {/* Open card */}
          <Reveal delay={180} className="md:col-span-6">
            <div className="flex h-full flex-col rounded-[20px] border border-line bg-[linear-gradient(160deg,rgba(77,163,255,0.1),transparent_55%),var(--color-s1)] p-6 md:p-9">
              <h3 className="text-[1.3rem] font-medium leading-tight tracking-[-0.03em]">
                Open, containerised, reproducible
              </h3>
              <p className="mt-2 max-w-[42ch] text-[15px] text-mut">
                Apache 2.0 code, a Dockerfile, a public Kaggle notebook and report tables
                generated straight from the JSON output.
              </p>
              <div className="mt-auto flex flex-wrap gap-2 pt-6">
                {["Apache 2.0", "Docker", "Kaggle", "Pretrained weights"].map((chip) => (
                  <span
                    key={chip}
                    className="rounded-full border border-line px-3.5 py-2 text-[13px] text-mut"
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
