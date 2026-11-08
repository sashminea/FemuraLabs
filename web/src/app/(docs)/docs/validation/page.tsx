import type { Metadata } from "next";

import { PageHeader } from "@/components/docs/page-header";
import { Bar } from "@/components/ui/bar";
import { Note } from "@/components/ui/note";
import { Table } from "@/components/ui/table";

export const metadata: Metadata = {
  title: "Validation report",
  description:
    "FemuraLabs validation: 4-fold cross-validation Dice for SegResNet, landmark errors and HKA, mLDFA and MPTA angle errors.",
};

const CV_ROWS = [
  { bone: "Femur", dice: 0.94, sd: "0.06", hd95: "1.50 mm", pct: 94 },
  { bone: "Tibia", dice: 0.91, sd: "0.06", hd95: "3.84 mm", pct: 91 },
  { bone: "Fibula", dice: 0.91, sd: "0.04", hd95: "1.50 mm", pct: 91 },
  { bone: "Talus", dice: 0.92, sd: "0.03", hd95: "2.69 mm", pct: 92 },
  { bone: "Overall", dice: 0.922, sd: "0.051", hd95: "—", pct: 92.2, total: true },
];

export default function ValidationPage() {
  return (
    <article className="prose-docs max-w-3xl">
      <PageHeader
        crumb="Validation"
        title="Validation report"
        lead="Segmentation, landmark and angle accuracy on 8 cadaveric subjects from the VSDFullBodyBoneReconstruction dataset, compared against landmarks placed by hand in 3D Slicer."
      />

      <div className="mt-10 grid grid-cols-1 border-y border-line md:grid-cols-3">
        {[
          ["0.922", "Mean Dice, 4-fold cross-validation"],
          ["0.98°", "Mean HKA error, clean 6 subjects"],
          ["1.5 mm", "Median HD95, femur and fibula"],
        ].map(([num, label], i) => (
          <div
            key={label}
            className={`py-8 ${i > 0 ? "md:border-l md:border-line md:pl-6" : "md:pr-6"}`}
          >
            <b className="block text-[clamp(2.6rem,5vw,4rem)] font-medium leading-none tracking-[-0.07em]">
              {num}
            </b>
            <span className="mt-3 block text-[13.5px] text-mut">{label}</span>
          </div>
        ))}
      </div>

      <h2 id="seg">Segmentation</h2>
      <p>
        A from-scratch 3D SegResNet (4.7M parameters) was cross-validated with 4 folds across all 8 subjects. Every subject was held out exactly once, with no data leakage.
      </p>
      <div className="mt-6 overflow-x-auto rounded-[20px] border border-line bg-white/[0.03] px-5 py-3.5 backdrop-blur-md">
        <table className="w-full min-w-[480px] border-collapse">
          <thead>
            <tr>
              {["Bone", "Mean Dice (4-fold CV)", "SD Dice", "Median HD95"].map((h) => (
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
            {CV_ROWS.map((r) => (
              <tr
                key={r.bone}
                className={r.total ? "border-t-2 border-line2" : "border-t border-line"}
              >
                <td className="px-5 py-5 align-middle text-[14.5px] text-tx">{r.bone}</td>
                <td className="px-5 py-5 align-middle text-[14.5px] text-mut">
                  <b className="text-[clamp(1.4rem,2.6vw,2rem)] font-medium tracking-[-0.05em] text-tx">
                    {r.dice.toFixed(3)}
                  </b>
                  <Bar width={r.pct} />
                </td>
                <td className="px-5 py-5 align-middle text-[14.5px] text-mut">{r.sd}</td>
                <td className="px-5 py-5 align-middle text-[14.5px] text-mut">{r.hd95}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        The overall mean Dice is <b>0.922 ± 0.051</b>. The median HD95 surface error is 1.5 to 4.5 mm, so the segmentations are close to the reference surface as well as overlapping it.
      </p>

      <h3 id="folds">Fold layout</h3>
      <p>
        Produced by <code>femuralabs ml cv</code>.
      </p>
      <Table
        headers={["Fold", "Train", "Validate"]}
        rows={[
          {
            cells: [
              "fold1",
              <code key="1">case03 to case08</code>,
              <code key="2">case01, case02</code>,
            ],
          },
          {
            cells: [
              "fold2",
              <code key="3">case01, 02, 05, 06, 07, 08</code>,
              <code key="4">case03, case04</code>,
            ],
          },
          {
            cells: [
              "fold3",
              <code key="5">case01, 02, 03, 04, 07, 08</code>,
              <code key="6">case05, case06</code>,
            ],
          },
          {
            cells: [
              "fold4",
              <code key="7">case01 to case06</code>,
              <code key="8">case07, case08</code>,
            ],
          },
        ]}
      />

      <h2 id="landmarks">Landmark errors</h2>
      <p>
        Automatic landmark rules against hand-placed landmarks. Two subjects have severe metal artifacts or extreme post-mortem deformation, so they are reported separately.
      </p>
      <Table
        headers={["Landmark", "Mean error, clean 6", "Mean error, all 8", "Hand repeat"]}
        rows={[
          { cells: ["Femoral head", "2.6 to 2.7 mm", "6.5 to 9.7 mm", "4 to 6 mm"] },
          { cells: ["Knee centre", "4.3 mm", "4.9 to 5.3 mm", "3 to 5 mm"] },
          { cells: ["Ankle centre", "5.6 to 6.9 mm", "6.0 to 7.3 mm", "about 2 mm"] },
        ]}
      />
      <Note>
        <p>
          Cases 04 and 06 fail at 26 to 36 mm because of deformation and metal, and are excluded from the clean column. The femoral head fit is inside the hand repeat distance on clean anatomy. The knee rule is within 5 mm on 11 of 16 knees.
        </p>
      </Note>

      <h2 id="angles">Alignment angles</h2>
      <p>Mean absolute error against hand-placed landmarks.</p>
      <Table
        headers={["Angle", "n", "Mean abs, all 8", "Mean abs, clean 6"]}
        rows={[
          { cells: ["HKA, right (coronal)", "8", "1.65°", "0.98°"] },
          { cells: ["HKA, left (coronal)", "8", "1.26°", "0.98°"] },
          { cells: ["mLDFA, right", "8", "1.23°", "0.82°"] },
          { cells: ["MPTA, right", "8", "0.62°", "0.58°"] },
        ]}
      />
      <p>
        On the clean subjects the coronal HKA error is about 1°, comparable to inter-observer spread and well inside the 5 to 10° corrections typical of high tibial osteotomy.
      </p>
      <Note warn>
        <p>
          <b>Caveat.</b> The joint-line points are the same hand clicks in the automatic and hand computations. mLDFA and MPTA therefore measure the mechanical-axis contribution, not the accuracy of an automatic joint-line detector.
        </p>
      </Note>

      <h2 id="baseline">TotalSegmentator baseline</h2>
      <p>
        TotalSegmentator against the human reference, run at 3 mm <code>--fast</code> on cropped CTs. The reference masks are cortical shells with the medullary canal unannotated, so TotalSegmentator fills an interior the human did not trace.
      </p>
      <Table
        headers={["Bone", "Dice, filled ref", "Dice, unfilled ref", "Mean HD95"]}
        rows={[
          { cells: ["Femur", "0.94", "0.72", "2.8 mm"] },
          { cells: ["Tibia", "0.90", "0.66", "5.5 mm"] },
          { cells: ["Fibula", "0.82", "0.73", "2.5 mm"] },
        ]}
      />
      <p>
        The filled Dice of 0.94 is the honest outer-surface agreement. The unfilled 0.72 measures the annotation-protocol difference, hollow versus solid.
      </p>

      <h2 id="limits">Limitations</h2>
      <div className="mt-6 grid gap-6 md:grid-cols-3">
        {[
          ["Small cohort", "Eight cadaveric subjects, one annotator. Results are descriptive and a proof of concept."],
          ["Post-mortem, supine", "Geometry differs from a standing, weight-bearing patient."],
          ["Metal artifacts", "One subject has bilateral total hip and knee arthroplasties. Beam hardening shatters the masks and the femoral head fit fails."],
          ["Post-mortem deformation", "One subject has extreme axial rotation and widened joint spaces, so the knee and ankle rules struggle."],
          ["Reference noise", "Condyle and plateau points were placed by surface click, repeating only to within 7 to 9 mm."],
          ["Checkpoint selection", "The released model was trained on 6 subjects and checkpoint-selected on the same 2 validation subjects, so results may carry a slight optimism bias."],
          ["Single dataset", "Cross-validated on all 8 subjects, but untested on external hospital data."],
        ].map(([title, body]) => (
          <div key={title} className="border-t border-line2 pt-5">
            <h3 className="!mt-0 text-[1.05rem] font-medium">{title}</h3>
            <p className="mt-2 text-sm">{body}</p>
          </div>
        ))}
      </div>
      <Note warn>
        <p>Research prototype. Not for clinical use or diagnosis.</p>
      </Note>
    </article>
  );
}
