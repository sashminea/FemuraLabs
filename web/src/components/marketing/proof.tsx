import { Bar } from "@/components/ui/bar";
import { CountUp } from "@/components/ui/count-up";
import { Reveal } from "@/components/ui/reveal";

const ROWS = [
  { bone: "Femur", dice: 0.94, sd: 0.06, hd95: "1.50 mm", pct: 94 },
  { bone: "Tibia", dice: 0.91, sd: 0.06, hd95: "3.84 mm", pct: 91 },
  { bone: "Fibula", dice: 0.91, sd: 0.04, hd95: "1.50 mm", pct: 91 },
  { bone: "Talus", dice: 0.92, sd: 0.03, hd95: "2.69 mm", pct: 92 },
  { bone: "Overall", dice: 0.922, sd: 0.051, hd95: "—", pct: 92.2, total: true },
];

const ANGLES = [
  { label: "HKA, right", value: 0.98 },
  { label: "HKA, left", value: 0.98 },
  { label: "mLDFA, right", value: 0.82 },
  { label: "MPTA, right", value: 0.58 },
];

export function Proof() {
  return (
    <section id="proof" className="py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <h2 className="max-w-[14ch] text-[clamp(2rem,4.8vw,3.8rem)] font-medium leading-[1.04] tracking-[-0.055em]">
            Accuracy against hand-placed landmarks.
          </h2>
        </Reveal>

        <Reveal delay={80}>
          <div
            data-cursor="card"
            className="mt-14 overflow-x-auto rounded-[20px] border border-line bg-white/[0.03] px-5 py-3.5 backdrop-blur-md"
          >
            <table className="w-full min-w-[480px] border-collapse">
              <thead>
                <tr>
                  {["Bone", "Dice score (4-fold CV)", "Median HD95"].map((h) => (
                    <th
                      key={h}
                      className="whitespace-nowrap px-5 pt-4 pb-3.5 text-left font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-dim"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((row) => (
                  <tr
                    key={row.bone}
                    className={row.total ? "border-t-2 border-line2" : "border-t border-line"}
                  >
                    <td className="px-5 py-5 align-middle text-[14.5px] text-tx">
                      {row.bone}
                    </td>
                    <td className="px-5 py-5 align-middle text-[14.5px] text-mut">
                      <b className="text-[clamp(1.4rem,2.6vw,2rem)] font-medium tracking-[-0.05em] text-tx">
                        <CountUp value={row.dice} decimals={3} />
                      </b>
                      <em className="ml-2.5 font-mono text-[13px] not-italic text-dim">
                        ± {row.sd.toFixed(3)}
                      </em>
                      <Bar width={row.pct} />
                    </td>
                    <td className="whitespace-nowrap px-5 py-5 align-middle text-[14.5px] text-mut">
                      {row.hd95}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Reveal>

        <Reveal delay={160}>
          <div className="mt-12 grid grid-cols-2 border-y border-line md:grid-cols-4">
            {ANGLES.map((a, i) => (
              <div
                key={a.label}
                className={`py-7 px-5 ${i === 0 ? "md:pl-0" : "md:border-l md:border-line"}`}
              >
                <b className="block text-[clamp(2.4rem,5vw,4.4rem)] font-medium leading-none tracking-[-0.07em]">
                  <CountUp value={a.value} decimals={2} suffix="°" />
                </b>
                <span className="mt-2.5 block text-sm text-mut">{a.label}</span>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal delay={200}>
          <p className="mt-6 max-w-[70ch] text-[13px] text-dim">
            Mean absolute angle error against hand-placed landmarks, on the six clean
            subjects, well inside the 5–10° corrections of high tibial osteotomy.
            Segmentation: all 8 subjects, each held out exactly once.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
