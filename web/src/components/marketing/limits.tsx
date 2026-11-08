import { Reveal } from "@/components/ui/reveal";

const LIMITS = [
  {
    title: "Small cohort",
    body: "Eight cadaveric subjects, one annotator. Results are descriptive, a proof of concept.",
  },
  {
    title: "Post-mortem, supine",
    body: "Geometry differs from a standing patient. Metal implants and deformation break the rules on two subjects.",
  },
  {
    title: "One dataset",
    body: "Cross-validated on all 8 subjects, but untested on external hospital data.",
  },
];

export function Limits() {
  return (
    <section id="limits" className="py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <h2 className="max-w-[14ch] text-[clamp(2rem,4.8vw,3.8rem)] font-medium leading-[1.04] tracking-[-0.055em]">
            What this does not claim.
          </h2>
        </Reveal>
        <Reveal delay={80}>
          <div className="mt-12 grid gap-6 md:grid-cols-3 md:gap-10">
            {LIMITS.map((l) => (
              <div key={l.title} className="border-t border-line2 pt-5">
                <h3 className="text-[1.1rem] font-medium tracking-[-0.03em]">{l.title}</h3>
                <p className="mt-2 text-sm text-mut">{l.body}</p>
              </div>
            ))}
          </div>
        </Reveal>
        <Reveal delay={160}>
          <p className="mt-10 text-sm text-amber">
            Research prototype. Not for clinical use or diagnosis.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
