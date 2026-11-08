import { Reveal } from "@/components/ui/reveal";

export function Problem() {
  return (
    <section id="problem" className="py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <p className="max-w-[22ch] text-[clamp(1.8rem,4.2vw,3.4rem)] font-medium leading-[1.1] tracking-[-0.05em] text-dim">
            Limb alignment is still measured by{" "}
            <b className="text-tx">clicking points by hand</b>. It is slow, and it varies from person to person.
          </p>
        </Reveal>

        <div className="mt-16 grid grid-cols-1 border-t border-line md:mt-24 md:grid-cols-2">
          <Reveal>
            <div className="pt-8 md:pr-8">
              <h3 className="mb-4 text-[clamp(1.8rem,3.4vw,2.8rem)] font-medium leading-none tracking-[-0.05em] text-dim">
                By hand
              </h3>
              <ul>
                {[
                  "Hours of segmentation in Slicer",
                  "Landmarks differ by 4–6 mm between repeats",
                  "Mirrored legs raise no error",
                ].map((item) => (
                  <li
                    key={item}
                    className="border-t border-line py-3 text-[15px] text-dim line-through decoration-white/[0.18]"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={120}>
            <div className="pt-8 md:border-l md:border-line md:pl-8">
              <h3 className="mb-4 bg-gradient-to-r from-tx to-blue bg-clip-text text-[clamp(1.8rem,3.4vw,2.8rem)] font-medium leading-none tracking-[-0.05em] text-transparent">
                FemuraLabs
              </h3>
              <ul>
                {[
                  "Segmentation in one command",
                  "Landmarks from mesh geometry",
                  "Explicit side checks, one sign convention",
                ].map((item) => (
                  <li
                    key={item}
                    className="border-t border-line py-3 text-[15px] text-mut"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
