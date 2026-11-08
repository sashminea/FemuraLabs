import { withOg } from "@/lib/og";
import Link from "next/link";

import { PageHeader } from "@/components/docs/page-header";
import { Note } from "@/components/ui/note";
import { Table } from "@/components/ui/table";
import { site } from "@/lib/site";

export const metadata = withOg(
  "architecture",
  "How it works",
  "How FemuraLabs works: SegResNet segmentation, mesh extraction, geometry rules and alignment angles.",
);

const FLOW = [
  { title: "CT volume", sub: "Real millimetres, LPS frame" },
  { title: "SegResNet", sub: "Femur, tibia, fibula, talus" },
  { title: "3D meshes", sub: "Watertight surfaces" },
  { title: "Landmarks", sub: "Hip, knee, ankle centres" },
  { title: "Angles", sub: "HKA, mLDFA, MPTA" },
];

const GEOMETRY = [
  {
    mono: "Hip",
    title: "Sphere fit",
    body: "The femoral head centre comes from a least-squares sphere fitted to the medial part of the top of the femur.",
  },
  {
    mono: "Knee",
    title: "Box rule",
    body: "The knee centre uses the bounding box of a thin axial slab 15 mm above the lowest femoral point, shifted by lateral and anterior offsets fitted to human placement conventions. This avoids the failure where one condyle sits lower than the other.",
  },
  {
    mono: "Ankle",
    title: "Plafond",
    body: "The rule finds the tibial plafond, the flat underside of the shin bone, and takes the midpoint between the inner and outer ankle bones at that level.",
  },
  {
    mono: "Limit",
    title: "Plafond stands in for the talus",
    body: "The talus is segmented and merged, but the ankle rule does not use it yet. It uses the plafond as a stand-in for the talar dome.",
  },
];

export default function ArchitecturePage() {
  return (
    <article className="prose-docs max-w-3xl">
      <PageHeader
        crumb="Architecture"
        title="How it works"
        lead="One straight path from scan to report. Each stage writes plain files, so you can stop, inspect or swap any stage."
      />

      <h2 id="flow">Pipeline flow</h2>
      <div className="mt-6 grid gap-3.5 md:grid-cols-5">
        {FLOW.map((node) => (
          <div key={node.title} className="rounded-2xl border border-line bg-bg p-5">
            <b className="block text-[1.05rem] font-medium tracking-[-0.03em]">
              {node.title}
            </b>
            <span className="mt-1.5 block text-[13.5px] text-mut">{node.sub}</span>
          </div>
        ))}
      </div>
      <p className="mt-8">
        The reference segmentations in the dataset often trace only the outer cortical shell. The pipeline fills the medullary canal before meshing, so the mesh represents the whole bone. Each bone becomes a triangle mesh with marching cubes and is checked for watertightness.
      </p>

      <h2 id="frame">Coordinate frame</h2>
      <p>
        The CT is loaded together with its geometry. Voxel spacing, origin and orientation travel with the array, so every later number is in millimetres in one frame: <b>LPS</b>, the frame SimpleITK uses.
      </p>
      <Note warn>
        <p>
          Mixing up left and right here does not raise an error. It quietly gives you a mirrored leg, so the project checks sides explicitly in several places.
        </p>
      </Note>

      <h2 id="model">SegResNet</h2>
      <p>
        The segmentation model is a 3D SegResNet from MONAI, trained from scratch on cadaveric CT. It segments the femur, tibia, fibula and talus on each leg.
      </p>
      <div className="mt-6 grid grid-cols-2 gap-4 rounded-xl border border-line bg-s1 p-5 md:grid-cols-4">
        {[
          ["4.7M", "Parameters"],
          ["0.922", "Mean Dice, 4-fold CV"],
          ["1.5 mm", "Training spacing"],
          ["96", "Patch size"],
        ].map(([num, label]) => (
          <div key={label}>
            <b className="block text-[clamp(1.4rem,2.4vw,1.8rem)] font-medium tracking-[-0.05em]">
              {num}
            </b>
            <span className="mt-1.5 block text-[13px] text-mut">{label}</span>
          </div>
        ))}
      </div>
      <Table
        headers={["Setting", "Value"]}
        rows={[
          { cells: ["Architecture", "MONAI SegResNet, 3D, from scratch"] },
          { cells: ["Training spacing", "1.5 mm isotropic"] },
          { cells: ["Patch size", "96 (default)"] },
          { cells: ["Batch size", "2 (default)"] },
          {
            cells: [
              "Epochs",
              <>
                200 (default for <code>ml train</code>), 100 per fold for <code>ml cv</code>
              </>,
            ],
          },
          {
            cells: [
              "Validation",
              "Trained on 6 subjects and validated on 2, plus 4-fold cross-validation over all 8",
            ],
          },
          {
            cells: [
              "Training notebook",
              <Link key="k" href={site.kaggle} className="l">
                Public Kaggle notebook
              </Link>,
            ],
          },
        ]}
      />
      <p>
        At inference the model runs a sliding window over the CT, splits the left and right sides, and upsamples the result back to the scan's native grid. The output is the <code>combined_seg.nii</code> that <code>pipeline run</code> reads.
      </p>
      <p>
        See the{" "}
        <Link href="/docs/validation#seg" className="l">
          validation report
        </Link>{" "}
        for per-bone Dice and surface error.
      </p>

      <h2 id="geometry">Geometry rules</h2>
      <p>The landmark rules work on the meshes. Each leg gets three centres.</p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {GEOMETRY.map((g) => (
          <div key={g.title} className="rounded-2xl border border-line bg-s1 p-6">
            <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-dim">
              {g.mono}
            </span>
            <h3 className="!mt-3 mb-1.5 text-[1.15rem] font-medium">{g.title}</h3>
            <p className="text-[14.5px] text-mut">{g.body}</p>
          </div>
        ))}
      </div>

      <h2 id="angles">Angles</h2>
      <p>
        From the three centres per leg the pipeline computes the mechanical axes and these angles.
      </p>
      <Table
        headers={["Angle", "Plane", "Convention"]}
        rows={[
          { cells: ["HKA", "Coronal", "Positive for varus, negative for valgus"] },
          { cells: ["mLDFA", "Coronal", "Acute angle, 90° or less"] },
          { cells: ["MPTA", "Coronal", "Acute angle, 90° or less"] },
        ]}
      />
      <ul>
        <li>
          <b>HKA</b> is computed in the coronal plane, matching the clinical definition and the plane used for mLDFA and MPTA. It is positive for varus and negative for valgus.
        </li>
        <li>
          The side of the body is detected automatically, so the same sign means the same thing on the left and right leg.
        </li>
        <li>
          <b>mLDFA</b> and <b>MPTA</b> are reported as acute angles (90° or less).
        </li>
        <li>
          Everything for a case goes to one JSON summary. Report tables are generated from those summaries.
        </li>
      </ul>
      <p>
        The repository records the design choices and the alternatives that were rejected in{" "}
        <Link href={`${site.github}/blob/main/docs/decisions.md`} className="l">
          docs/decisions.md
        </Link>
        .
      </p>
    </article>
  );
}
