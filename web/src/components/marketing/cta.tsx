import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/ui/reveal";
import { site } from "@/lib/site";

export function Cta() {
  return (
    <section className="relative overflow-hidden py-24 text-center md:py-32">
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 bottom-[-40%] h-[560px] w-[1000px] -translate-x-1/2 bg-[radial-gradient(closest-side,rgba(77,163,255,0.22),transparent)]"
      />
      <div className="relative mx-auto max-w-7xl px-6">
        <Reveal>
          <h2 className="mx-auto max-w-[12ch] text-[clamp(2.6rem,7vw,6rem)] font-medium leading-[1.04] tracking-[-0.06em]">
            Rebuild the measurement yourself.
          </h2>
        </Reveal>
        <Reveal delay={120}>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button href="/docs">Read the Docs</Button>
            <Button href={site.github} variant="ghost" external>
              Get Started
            </Button>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
