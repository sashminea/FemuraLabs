import { withOg } from "@/lib/og";
import Link from "next/link";

import { PageHeader } from "@/components/docs/page-header";
import { Note } from "@/components/ui/note";
import { Table } from "@/components/ui/table";

export const metadata = withOg(
  "docs",
  "Simulator",
  "How the FemuraLabs high tibial osteotomy wedge simulator works and how to read its results.",
);

const OUTPUTS: [string, string][] = [
  ["Wedge gap", "The opening at the medial edge of the cut, in mm. It equals the tibia width at the cut plane times tan θ."],
  ["MPTA", "Medial proximal tibial angle after the correction. It is the pre-op value plus θ."],
  ["HKA", "Hip-knee-ankle angle after the correction. It moves toward valgus by one degree for every degree of θ."],
];

const TARGETS: [string, string, string][] = [
  ["Neutral", "−1° to +1°", "θ is set to the pre-op HKA"],
  ["Valgus 3°", "−4° to −2°", "θ is set to the pre-op HKA plus 3°"],
  ["Valgus 6°", "−7° to −5°", "θ is set to the pre-op HKA plus 6°"],
];

const LAYERS: [string, string][] = [
  ["Bones", "Femur, proximal tibia and distal tibia. An opacity slider (10% to 100%) lets you see the other layers through the bone."],
  ["Axes", "Femoral axis, the dashed femoral reference line, tibial axis and joint line."],
  ["Angles", "The HKA arc, the MPTA arc and the wedge triangle at the cut."],
  ["Markers", "The hip, knee and ankle centres and the lateral hinge."],
];

export default function SimulatorDocsPage() {
  return (
    <article className="prose-docs max-w-3xl">
      <PageHeader
        crumb="Reference"
        title="Simulator"
        lead="An interactive, geometric demonstration of a medial opening-wedge high tibial osteotomy, built on the 3D bones and landmarks that the pipeline produces from a real CT."
      />

      <Note warn>
        <p>Teaching demonstration. Not a surgical planning tool and not for clinical use.</p>
      </Note>

      <h2 id="what">What it models</h2>
      <p>
        A high tibial osteotomy (HTO) cuts the upper shin bone and opens a wedge on the inner (medial) side, leaving the outer (lateral) edge of the bone intact as a hinge. The lower part of the tibia pivots about that hinge, which straightens a bow-legged (varus) leg.
      </p>
      <p>
        The simulator treats the bones as rigid and rotates the distal tibia about the lateral hinge by the correction angle <b>θ</b>. The femur and the upper tibia do not move. Every number on screen is computed from the hip, knee, ankle and hinge positions of the loaded case, using the angle definitions described in the{" "}
        <Link href="/docs/architecture#angles" className="l">
          architecture notes
        </Link>
        .
      </p>

      <h2 id="controls">Controls</h2>
      <p>
        The <b>Correction</b> panel sets how far the wedge is opened.
      </p>
      <ul>
        <li>
          <b>Angle θ</b> runs from 0° to 15°. Drag the slider (steps of 0.5°) or type a value in the field (steps of 0.1°).
        </li>
        <li>
          <b>Target</b> picks the alignment you are aiming for and moves θ to the angle that reaches it.
        </li>
        <li>
          A green <b>target zone</b> on the slider marks the values of θ that land inside the selected target range.
        </li>
      </ul>
      <Table
        headers={["Target", "HKA range counted as on target", "What the target sets"]}
        rows={TARGETS.map(([name, range, sets]) => ({
          cells: [name, range, sets],
        }))}
      />
      <p>
        In the 3D view, drag to rotate and scroll to zoom. On a wide screen you can drag the dividers between the panels to resize them, and double-click a divider to reset it. On a narrow screen the panels become tabs below the 3D view.
      </p>

      <h2 id="results">Reading the results</h2>
      <p>
        The <b>Results</b> panel updates as you move the slider. Each value is shown next to the pre-op value it started from.
      </p>
      <Table
        headers={["Value", "Meaning"]}
        rows={OUTPUTS.map(([name, desc]) => ({
          cells: [name, desc],
        }))}
      />
      <p>
        A status label next to the results says whether the current HKA is <b>in target range</b>, <b>under-corrected</b> (the wedge is not open enough) or <b>over-corrected</b> (the leg has gone past the target). HKA is positive for varus and negative for valgus.
      </p>
      <p>
        The gap grows with tan θ, so it rises faster than the angle does. Large wedges are harder to heal, which is why smaller corrections that reach the target are usually preferred.
      </p>

      <h2 id="layers">Layers and the 3D view</h2>
      <p>
        The <b>Layers</b> panel switches parts of the 3D scene on and off. Hover a layer name to see what it is.
      </p>
      <Table
        headers={["Group", "What it contains"]}
        rows={LAYERS.map(([name, desc]) => ({
          cells: [name, desc],
        }))}
      />

      <h2 id="explainer">Explainer</h2>
      <p>
        The right-hand panel has a live commentary that describes the current state of the correction, and an <b>Ask about</b> list of short topics such as what HKA and MPTA mean, what the hinge does, and why the gap grows quickly. Terms with a dotted underline show a definition when you hover over them or tap them.
      </p>

      <h2 id="case">Case data</h2>
      <p>
        The simulator loads one case from the validation set. The bone meshes come from the segmentation and mesh steps of the pipeline, simplified so that they run smoothly in a browser. The pre-op HKA, the pre-op MPTA and the tibia width at the cut plane come from that case. The cut plane is fixed at 15 mm below the top of the tibia.
      </p>

      <h2 id="limits">What it does not model</h2>
      <ul>
        <li>Soft tissue, cartilage and ligament balance.</li>
        <li>Bone healing, bone graft and fixation hardware.</li>
        <li>Weight-bearing alignment, since the scan is post-mortem and supine.</li>
        <li>Tibial slope, and the centre of rotation of angulation (CORA) used in full surgical planning.</li>
      </ul>
      <p>
        The broader limits of the data are listed on the{" "}
        <Link href="/docs/validation#limits" className="l">
          validation page
        </Link>
        .
      </p>
    </article>
  );
}
