import { CountUp } from "@/components/ui/count-up";
import { Reveal } from "@/components/ui/reveal";

export function Stats() {
  return (
    <section id="stats" className="py-0">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <div className="grid grid-cols-1 border-y border-line md:grid-cols-3">
            <div className="border-line py-10 md:border-l md:first:border-l-0 md:first:pl-0 md:px-8">
              <b className="block text-[clamp(3rem,8vw,7rem)] font-medium leading-none tracking-[-0.07em]">
                <CountUp value={0.922} decimals={3} />
              </b>
              <span className="mt-3.5 block text-sm text-mut">
                Mean Dice, 4-fold cross-validation
              </span>
            </div>
            <div className="border-line py-10 md:border-l md:px-8">
              <b className="block text-[clamp(3rem,8vw,7rem)] font-medium leading-none tracking-[-0.07em]">
                <CountUp value={0.98} decimals={2} suffix="°" />
              </b>
              <span className="mt-3.5 block text-sm text-mut">
                Mean HKA error on clean subjects
              </span>
            </div>
            <div className="border-line py-10 md:border-l md:px-8">
              <b className="block text-[clamp(3rem,8vw,7rem)] font-medium leading-none tracking-[-0.07em]">
                <CountUp value={4.7} decimals={1} suffix="M" />
              </b>
              <span className="mt-3.5 block text-sm text-mut">
                Parameters, trained from scratch
              </span>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
