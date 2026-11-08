import { withOg } from "@/lib/og";
import Link from "next/link";

import { PageHeader } from "@/components/docs/page-header";
import { CodeBlock } from "@/components/ui/code-block";
import { Note } from "@/components/ui/note";
import { site } from "@/lib/site";

export const metadata = withOg(
  "quickstart",
  "Quickstart",
  "Install FemuraLabs, run SegResNet inference and the geometry pipeline.",
);

export default function QuickstartPage() {
  return (
    <article className="prose-docs max-w-3xl">
      <PageHeader
        crumb="Getting started"
        title="Quickstart"
        lead="Install FemuraLabs, segment a CT with the pretrained SegResNet, then turn the segmentation into meshes, landmarks and angles."
      />

      <h2 id="install">Install</h2>
      <p>
        Both the local Python environment and the container give you the{" "}
        <code>femuralabs</code> command.
      </p>

      <h3>Python</h3>
      <CodeBlock
        language="bash"
        code={`$ git clone ${site.github}.git
$ cd FemuraLabs
$ python3 -m venv .venv
$ source .venv/bin/activate   # Windows: .venv\\Scripts\\Activate.ps1
$ python -m pip install --upgrade pip
$ pip install -r requirements.txt
$ pip install -e .`}
      />

      <h3>Docker</h3>
      <CodeBlock
        language="bash"
        code={`$ docker build -t femuralabs-tool .
$ docker run --rm femuralabs-tool --help`}
      />

      <p>
        Verify the install. <code>doctor check</code> reports Python, Docker, SimpleITK, numpy, scikit-image, PyTorch, MONAI and whether a CUDA GPU is available. The test suite needs no data.
      </p>
      <CodeBlock
        language="bash"
        code={`$ femuralabs doctor check
$ pytest -q`}
      />
      <Note>
        <p>
          Add <code>--json</code> to <code>doctor check</code> for machine-readable output.
        </p>
      </Note>

      <h2 id="infer">Run inference</h2>
      <p>
        This turns a raw CT into a combined segmentation of the four bones on both legs.
      </p>

      <h3>Download the pretrained weights</h3>
      <p>
        The weights come from a GitHub Release and are saved to{" "}
        <code>~/.femuralabs/weights/</code>.
      </p>
      <CodeBlock language="bash" code={`$ femuralabs ml download-weights`} />

      <h3>Segment the scan</h3>
      <p>
        Sliding-window inference runs on the CT, splits left and right, and upsamples back to the native grid. <code>infer</code> uses the downloaded weights unless you pass <code>--checkpoint</code>.
      </p>
      <CodeBlock
        language="bash"
        code={`$ femuralabs ml infer \\
  --ct path/to/new_scan.nii \\
  --out data/raw/case01/combined_seg.nii`}
      />
      <Note>
        <p>
          If the checkpoint is missing, <code>infer</code> stops and tells you to run <code>download-weights</code> first.
        </p>
      </Note>

      <h2 id="geometry">Run the geometry pipeline</h2>
      <p>
        Feed the segmentation to <code>pipeline run</code>. <code>--angles</code> adds the alignment angles. <code>--fill</code> fills the medullary canal before meshing, which matters when the segmentation only traces the cortical shell.
      </p>
      <CodeBlock
        language="bash"
        code={`$ femuralabs pipeline run \\
  --case data/raw/case01/combined_seg.nii \\
  --out output/case01 \\
  --angles \\
  --fill`}
      />
      <p>
        To check the automatic landmarks against hand-placed ones, add{" "}
        <code>--compare</code> with a Slicer landmark file.
      </p>
      <CodeBlock
        language="bash"
        code={`$ femuralabs pipeline run \\
  --case data/raw/case07/combined_seg.nii \\
  --out output/case07 \\
  --compare data/ref/landmarks_case07.mrk.json \\
  --angles \\
  --fill`}
      />

      <h2 id="outputs">Read the outputs</h2>
      <p>
        Everything for a case is written under the <code>--out</code> folder, including the bone meshes and a <code>summary.json</code> with the landmarks and angles. HKA is reported in the coronal plane, positive for varus and negative for valgus. The full 3D angle is recorded as <code>HKA3D_&lt;side&gt;</code>.
      </p>
      <CodeBlock
        language="python"
        code={`import json

with open("output/case01/summary.json") as f:
    summary = json.load(f)

print(list(summary))`}
      />

      <h2 id="reproduce">Reproduce from the dataset</h2>
      <p>
        To rebuild the validation from scratch, prepare the data, place reference landmarks, then run the batch and report commands.
      </p>

      <h3>Merge or preprocess the segmentations</h3>
      <p>
        Standard lower-limb subjects ship as separate thigh and shank masks. Full-body subjects ship with an H5 transform.
      </p>
      <CodeBlock
        language="bash"
        code={`$ femuralabs data merge \\
  --thighs path/to/thighs.nii \\
  --shanks path/to/shanks.nii \\
  --out data/raw/case01/combined_seg.nii`}
      />
      <CodeBlock
        language="bash"
        code={`$ femuralabs data preprocess \\
  --ct path/to/SMIR.Body.nii \\
  --thighs-seg path/to/Pelvis-Thighs.seg.nrrd \\
  --shanks-seg path/to/Shanks-Feet.seg.nrrd \\
  --transform path/to/Transform-Upside-Down.h5 \\
  --out-dir data/raw/case01`}
      />

      <h3>Place reference landmarks</h3>
      <p>
        Each subject needs ten landmarks placed by hand in 3D Slicer and saved as <code>.mrk.json</code> in <code>data/ref/</code>. The{" "}
        <Link href={`${site.github}/blob/main/docs/landmarks.md`} className="l">
          placement guide
        </Link>{" "}
        covers every landmark.
      </p>

      <h3>Run every case</h3>
      <p>
        This writes <code>output/&lt;case&gt;/summary.json</code> for each case.
      </p>
      <CodeBlock language="bash" code={`$ femuralabs pipeline batch`} />

      <h3>Generate the report tables</h3>
      <p>
        The tables are generated from the JSON output, so the numbers cannot drift from the data.
      </p>
      <CodeBlock language="bash" code={`$ femuralabs pipeline report`} />
    </article>
  );
}
