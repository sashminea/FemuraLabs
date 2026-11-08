import type { Metadata } from "next";

import { CommandBlock } from "@/components/docs/command-block";
import { PageHeader } from "@/components/docs/page-header";
import { CodeBlock } from "@/components/ui/code-block";
import { Note } from "@/components/ui/note";
import { Table } from "@/components/ui/table";

export const metadata: Metadata = {
  title: "CLI reference",
  description:
    "Reference for every femuralabs CLI command: doctor, data, pipeline, ml and volume.",
};

const TOP_LEVEL: [string, string][] = [
  ["doctor", "Check system dependencies and environment."],
  ["data", "Dataset preparation and merging."],
  ["pipeline", "Geometry, landmarks, and angles."],
  ["ml", "Machine learning training and validation."],
  ["volume", "Volume geometry and synthetic data."],
  ["version", "Print the current version of FemuraLabs."],
];

export default function CliPage() {
  return (
    <article className="prose-docs max-w-3xl">
      <PageHeader
        crumb="CLI reference"
        title="CLI reference"
        lead="Every command in the femuralabs CLI, with its flags and defaults. Run any command with --help for the same information in your terminal."
      />

      <CodeBlock language="bash" code="$ femuralabs --help" />
      <Table
        headers={["Command", "Description"]}
        rows={TOP_LEVEL.map(([c, d]) => ({
          cells: [<code key={c}>{c}</code>, d],
        }))}
      />

      <CommandBlock
        name="doctor"
        subcommand="check"
        description="Verify that core dependencies and GPU are available."
        example={`$ femuralabs doctor check
$ femuralabs doctor check --json`}
        flags={[{ flag: "--json", default: "off", description: "Output as JSON." }]}
        extra={
          <p>
            Checks for <code>python</code> and <code>docker</code> on your PATH, imports SimpleITK, numpy, skimage, torch and monai, and reports whether a CUDA GPU is available. Without a GPU it reports that it is using the CPU.
          </p>
        }
      />

      <h2 id="data">data</h2>
      <p>Dataset preparation and merging.</p>

      <CommandBlock
        name="data"
        subcommand="inventory"
        description="Scan a directory for DICOM, NRRD and NIfTI files and list them."
        example="$ femuralabs data inventory --dir data/raw"
        flags={[{ flag: "--dir, -d", default: "", description: "Directory to scan.", required: true }]}
      />

      <CommandBlock
        name="data"
        subcommand="merge"
        description="Merge Slicer-exported thighs and shanks into an 8-label combined mask."
        example={`$ femuralabs data merge \\
  --thighs thighs.nii --shanks shanks.nii \\
  --out data/raw/case01/combined_seg.nii`}
        flags={[
          { flag: "--thighs", default: "", description: "Path to thighs NIfTI.", required: true },
          { flag: "--shanks", default: "", description: "Path to shanks NIfTI.", required: true },
          { flag: "--out", default: "", description: "Output combined_seg.nii.", required: true },
        ]}
      />

      <CommandBlock
        name="data"
        subcommand="preprocess"
        description="Apply the H5 transform, crop, and centre a full-body subject."
        example={`$ femuralabs data preprocess \\
  --ct SMIR.Body.nii \\
  --thighs-seg Pelvis-Thighs.seg.nrrd \\
  --shanks-seg Shanks-Feet.seg.nrrd \\
  --transform Transform-Upside-Down.h5 \\
  --out-dir data/raw/case01`}
        flags={[
          { flag: "--ct", default: "", description: "Full-body CT (.nii).", required: true },
          { flag: "--thighs-seg", default: "", description: "Thighs segmentation (.seg.nrrd).", required: true },
          { flag: "--shanks-seg", default: "", description: "Shanks segmentation (.seg.nrrd).", required: true },
          { flag: "--transform", default: "", description: "H5 transform file.", required: true },
          { flag: "--out-dir", default: "", description: "Output directory.", required: true },
        ]}
      />

      <h2 id="pipeline">pipeline</h2>
      <p>Geometry, landmarks, and angles.</p>

      <CommandBlock
        name="pipeline"
        subcommand="run"
        description="Run mesh extraction, landmarks, and angles for one case."
        example={`$ femuralabs pipeline run \\
  --case data/raw/case07/combined_seg.nii \\
  --out output/case07 \\
  --compare data/ref/landmarks_case07.mrk.json \\
  --angles --fill`}
        flags={[
          { flag: "--case", default: "", description: "Path to combined_seg.nii.", required: true },
          { flag: "--out", default: "", description: "Output directory.", required: true },
          { flag: "--compare", default: "none", description: "Optional path to a landmarks.mrk.json reference." },
          { flag: "--angles", default: "off", description: "Compute alignment angles." },
          { flag: "--fill", default: "off", description: "Fill medullary canals before meshing." },
        ]}
      />

      <CommandBlock
        name="pipeline"
        subcommand="batch"
        description="Run the pipeline on every case in the data directory."
        example="$ femuralabs pipeline batch"
        flags={[
          { flag: "--data-dir", default: "data/raw", description: "Directory containing case folders." },
          { flag: "--out-dir", default: "output", description: "Output directory." },
        ]}
        extra={
          <Note>
            <p>
              The batch command currently launches the batch script without forwarding these two options, so the script reads <code>data/raw</code> and writes <code>output</code>.
            </p>
          </Note>
        }
      />

      <CommandBlock
        name="pipeline"
        subcommand="report"
        description="Generate markdown tables from the JSON outputs."
        example="$ femuralabs pipeline report"
        extra={
          <p>
            Writes <code>reports/landmark_errors.md</code> and <code>reports/angles_case.md</code>.
          </p>
        }
      />

      <h2 id="ml">ml</h2>
      <p>Machine learning training and validation.</p>

      <CommandBlock
        name="ml"
        subcommand="download-weights"
        description="Download the pretrained SegResNet weights from the GitHub Release."
        example="$ femuralabs ml download-weights"
        extra={
          <p>
            Saves <code>femuralabs_segresnet_v1.pt</code> to <code>~/.femuralabs/weights/</code>. If the download is a zip, it is extracted into the same folder.
          </p>
        }
      />

      <CommandBlock
        name="ml"
        subcommand="prepare"
        description="Extract, fill, and resample full volumes to .npy for ML training."
        example="$ femuralabs ml prepare --out-dir data/ml_npy"
        flags={[
          { flag: "--out-dir", default: "data/ml_npy", description: "Output directory for .npy files." },
          { flag: "--spacing", default: "1.5", description: "Isotropic resampling spacing in mm." },
        ]}
      />

      <CommandBlock
        name="ml"
        subcommand="train"
        description="Train the SegResNet model. Needs a GPU."
        example={`$ femuralabs ml train \\
  --data-dir data/ml_npy \\
  --out-dir runs/run1 \\
  --patch 96 --batch-size 2 --epochs 200`}
        flags={[
          { flag: "--data-dir", default: "", description: "Directory containing .npy files.", required: true },
          { flag: "--out-dir", default: "", description: "Output directory for checkpoints.", required: true },
          { flag: "--patch", default: "96", description: "Patch size." },
          { flag: "--batch-size", default: "2", description: "Batch size." },
          { flag: "--epochs", default: "200", description: "Number of epochs." },
          { flag: "--resume", default: "off", description: "Resume from last.pt." },
        ]}
      />

      <CommandBlock
        name="ml"
        subcommand="validate"
        description="Run sliding-window inference and compute Dice and HD95."
        example={`$ femuralabs ml validate \\
  --checkpoint runs/run1/best.pt \\
  --data-dir data/ml_npy \\
  --cases case07,case08`}
        flags={[
          { flag: "--checkpoint", default: "", description: "Path to best.pt.", required: true },
          { flag: "--data-dir", default: "", description: "Directory containing .npy files.", required: true },
          { flag: "--out-dir", default: "reports/data", description: "Output directory for JSON results." },
          { flag: "--cases", default: "case07,case08", description: "Comma-separated validation cases." },
        ]}
      />

      <CommandBlock
        name="ml"
        subcommand="infer"
        description="Run sliding-window inference on a raw CT to produce a combined_seg.nii."
        example={`$ femuralabs ml infer \\
  --ct path/to/new_scan.nii \\
  --out data/raw/case01/combined_seg.nii`}
        flags={[
          { flag: "--ct", default: "", description: "Path to a raw CT (.nii or .nrrd).", required: true },
          { flag: "--out", default: "", description: "Output path for combined_seg.nii.", required: true },
          { flag: "--checkpoint", default: "~/.femuralabs/weights/femuralabs_segresnet_v1.pt", description: "Path to model weights." },
        ]}
      />

      <CommandBlock
        name="ml"
        subcommand="cv"
        description="Run 4-fold cross-validation on the 8 subjects. Trains and validates each fold in turn."
        example="$ femuralabs ml cv --data-dir data/ml_npy"
        flags={[
          { flag: "--data-dir", default: "", description: "Directory containing .npy files.", required: true },
          { flag: "--out-dir", default: "runs/cv", description: "Output directory for folds." },
          { flag: "--epochs", default: "100", description: "Epochs per fold." },
          { flag: "--patch", default: "96", description: "Patch size." },
          { flag: "--batch-size", default: "2", description: "Batch size." },
        ]}
        extra={<p>Each fold holds out two subjects for validation and trains on the other six.</p>}
      />

      <h2 id="volume">volume</h2>
      <p>Volume geometry and synthetic data.</p>

      <CommandBlock
        name="volume"
        subcommand="info"
        description="Print the geometry of a synthetic or saved volume."
        example="$ femuralabs volume info --file volume.npy --out reports/volume"
        flags={[
          { flag: "--file, -f", default: "none", description: "Path to a .npy volume. Omit to generate a synthetic one." },
          { flag: "--shape", default: "4 6 6", description: "Shape for the synthetic volume (z y x)." },
          { flag: "--spacing", default: "2.0 1.0 1.0", description: "Spacing in mm (z y x)." },
          { flag: "--out", default: "none", description: "Folder to write info.json." },
        ]}
        extra={<p>Prints a table with shape, spacing, dtype and extent in millimetres.</p>}
      />

      <h2 id="version">version</h2>
      <p>Print the current version of FemuraLabs.</p>
      <CodeBlock language="bash" code="$ femuralabs version" />
    </article>
  );
}
