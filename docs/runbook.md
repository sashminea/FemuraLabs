# Runbook

Every command in this document was typed and its output captured on the
workstation used to develop this repository. GUI procedures describe what
was clicked; the file sizes and command outputs are real, not typical.
Each section states what a stage does, what output to expect, what the step
proves, and what a failure means.

Nothing here requires a GPU. The container stages use the CPU only.


## Environment setup

Run this before any other command in a new terminal. The three checks
confirm the shell is in the project root, the virtual environment is active,
and no unexpected files are modified.

    cd ~/FemuraLabs
    source .venv/bin/activate
    pwd
    which python
    git status

Expected:

- `pwd` ends in `FemuraLabs`.
- `which python` contains `.venv`.
- `git status` reports either `nothing to commit` or only files intended
  for change.

If `pwd` is wrong, later commands fail for unrelated reasons — a `pytest`
run from the wrong folder often collects nothing, and a `docker build .`
from the wrong folder copies the wrong context. If `which python` does not
contain `.venv`, packages install into the system Python, not the project
one.

On Windows the activation command is `.venv\Scripts\Activate.ps1`.


## Running the test suite

The suite tests the array helpers, the training utilities, the CLI, the
report writer, and the verdict rule against hand-computed results. It is
fast and it is the cheapest check that the existing behaviour is intact.

    pytest -q

Expected: one line ending with `passed`, no line containing `failed`.
The count varies as tests are added; `conftest.py` at the project root puts
`src/` on the import path, so no `PYTHONPATH` prefix is needed.

If a test fails, the output names the file and line of the failed
assertion. Do not change the test to match the code; change the code, or
add an entry to `docs/decisions.md` explaining why the expected value was
wrong.


## Statistics summary tool

Reads a `.npy` file and prints shape, dtype, min, max and mean. Smallest
end-to-end test of the installed package.

    mkdir -p data
    python -c 'import numpy as np; np.save("data/small.npy", np.arange(6, dtype=np.float32).reshape(2,3))'
    PYTHONPATH=src python -m femuralabs.toolkit.summary data/small.npy

Expected:

    shape: (2, 3)
    dtype: float32
    min: 0.00
    max: 5.00
    mean: 2.50

The six numbers 0–5 sum to 15, so a mean of 2.50 is checkable by hand
without trusting the tool.

If the command fails with `ModuleNotFoundError: No module named
'femuralabs'`, `PYTHONPATH=src` was omitted. If it fails with
`FileNotFoundError`, `data/small.npy` was not created — re-run the second
line from the project root.


## Training the small CNN

Trains `SmallCNN` on MNIST for a few epochs. First run downloads the MNIST
data into `data/` (a few MB). Each run writes one folder under `runs/`,
named by `--run-name`, containing `config.json`, `environment.json`,
`metrics.csv` and `best.pt`.

    PYTHONPATH=src python scripts/train_small_cnn.py \
        --seed 0 --epochs 5 \
        --run-name run_a_s0 \
        --commit "$(git describe --always --dirty)"

Expected: one line per epoch with training loss, validation loss and
accuracy, then a PNG in `reports/run_a_s0_curves.png`.

The `$(...)` runs `git describe` before the script starts, so
`config.json` records the exact commit. A `-dirty` suffix in the hash is a
warning: the run was started from an uncommitted tree, and the recorded
commit is not the code that actually ran.

`environment.json` is written by `train_utils.environment_record()`. It
records Python, numpy, torch and torchvision versions, the OS, CPU count
and (when a GPU is used) the GPU name. If a future run gives different
numbers, comparing the two `environment.json` files shows whether a
package update is the cause.

Do not reuse a run name; `runs/<name>/` is overwritten. For three seeds of
one variant, use `run_a_s0`, `run_a_s1`, `run_a_s2`.

On Windows PowerShell, replace `PYTHONPATH=src python` with a separate
line `$env:PYTHONPATH = "src"` before the `python` call, and replace
`"$(git describe ...)"` with `(git describe --always --dirty)`.


## Building the tool container

Builds the `toolkit-hello` image. The image installs numpy only and runs
`scripts/hello_pipeline.py` on start, so it is the deliverable that
executes the project without depending on the host Python.

    docker build -t toolkit-hello .

`-t` names the image (tag defaults to `latest`). The final `.` is the
build context — the folder the build is allowed to copy from. It is the
project root, not `scripts/`.

Expected: the build ends with a line naming the image, for example
`=> naming to docker.io/library/toolkit-hello:latest`. The first build
pulls the base image and installs numpy, so it takes a minute or two.
Rebuilds reuse the cached dependency layer and finish in a few seconds.

If Docker reports `Cannot connect to the Docker daemon`, Docker Desktop is
not running. If `COPY` fails with `file not found`, the missing file is
either untracked or excluded by `.dockerignore`; check `git status` first
and the ignore file second.


## Running the tool container

    docker run --rm toolkit-hello

Expected:

    shape (z, y, x): (4, 6, 6)
    spacing (mm): (2.0, 1.0, 1.0)
    dtype: float32
    extent (mm): (8.0, 6.0, 6.0)

Any words after the image name replace the container's default command
completely. Three examples:

    # different shape and spacing
    docker run --rm toolkit-hello python -m femuralabs.toolkit.cli --shape 3 5 5 --spacing 1.5 1.5 1.5

    # which account does the container use?
    docker run --rm toolkit-hello id
    # expected: uid=1000(student) gid=1000(student) groups=1000(student)

    # start the service on host port 8000
    docker run --rm -p 8000:8000 toolkit-hello python -m femuralabs.toolkit.service.serve
    # in a second terminal:  curl http://localhost:8000/health

`--rm` deletes the container when it stops; without it, stopped containers
accumulate and `docker ps -a` lists them. `-p 8000:8000` forwards host
port 8000 to container port 8000 (host:container order). If it errors with
`port is already allocated`, another program holds 8000 — publish to
`-p 8001:8000` and `curl :8001` instead.


## Mounting data in and results out

The container reads a host folder marked read-only and writes results to a
second host folder. The image holds neither folder; both live on the host.

Create the input volume by calling the shared `make_volume` — the same
function used by `hello_pipeline.py` and the CLI's `--shape` path:

    PYTHONPATH=src python -c 'import numpy as np; from femuralabs.toolkit.volume_info import make_volume; v, _ = make_volume((2,3,4), (3.0,1.0,1.0)); np.save("data/volume.npy", v)'

Create the output folder as the host user before the container starts.
Docker creates a missing bind-mount folder as `root`; a pre-created folder
belongs to the host user (UID 1000 by default in WSL2), matching the
container's `student` account:

    mkdir -p output
    ls -la output                # owner should be your host user

Run with two mounts — data read-only, output writable:

    docker run --rm \
      -v "$(pwd)/data:/data:ro" \
      -v "$(pwd)/output:/output" \
      toolkit-hello \
      python -m femuralabs.toolkit.cli \
        --file /data/volume.npy \
        --spacing 3 1 1 \
        --out /output

Expected:

    shape (z, y, x): (2, 3, 4)
    spacing (mm): (3.0, 1.0, 1.0)
    dtype: float32
    extent (mm): (6.0, 3.0, 4.0)
    wrote: /output/info.json

The `wrote:` line names the **container** path. The host file is:

    cat output/info.json
    ls -la output/               # owner should be your host user, not root

Read-only is enforced — attempting to write into `/data` fails:

    docker run --rm -v "$(pwd)/data:/data:ro" toolkit-hello \
      python -c "open('/data/test.txt', 'w').write('x')"
    # OSError: [Errno 30] Read-only file system

A mount hides what the image holds at the mount path:

    docker run --rm -v "$(pwd)/data:/app/src:ro" toolkit-hello \
      python -m femuralabs.toolkit.cli
    # No module named 'femuralabs'

Failure modes:

- `No such file or directory: /data/volume.npy` — the host path in the
  flag was wrong; Docker silently created an empty folder there.
- `Permission denied` on `/output` — the host folder is owned by root, not
  UID 1000. `rm -rf output && mkdir -p output` before the run.
- `Read-only file system` on `/output` — `--out` points into `/data`. Use
  `/output` for `--out`.
- `No module named 'femuralabs'` — a mount overlaps `/app/src` or `/app`,
  hiding the code. Use `/data` and `/output`.

`output/` and `data/` are ignored by git.


## Running both services with Compose

Starts the API and the static web page together on one private network
with one command. Both are published on the host, so a browser and `curl`
reach them by port.

Before the first start:

    mkdir -p web output
    docker compose config

`config` validates the file and prints it with every default filled in. If
the output is a YAML parse error naming a line and column, there is a tab
or a wrong indent — YAML forbids tabs.

Start, inspect, request, stop:

    docker compose up --build -d
    docker compose ps
    curl http://localhost:8000/health
    curl http://localhost:8000/info
    curl -I http://localhost:8080/
    docker compose logs api
    docker compose down

Expected:

- `up` creates the network `femuralabs_default` and starts `api` and `web`.
- `ps` lists both, each with `0.0.0.0:8000->8000/tcp` and
  `0.0.0.0:8080->8080/tcp`.
- `curl` on port 8000 `/health` gives `{"status": "ok"}`.
- `curl` on port 8000 `/info` gives the content of `output/info.json` if
  it exists, or the four-key geometry dictionary if not.
- `curl -I` on port 8080 gives `HTTP/1.0 200 OK` and a `Content-type:
  text/html` header.
- `logs api` shows `serving on 0.0.0.0:8000`.
- `down` removes both containers and the network. `output/` and `web/`
  survive — they are bind mounts on the host.

Recreate the report if `/info` returns the fallback shape `(4, 6, 6)`
rather than the report's shape — `output/info.json` is missing:

    PYTHONPATH=src python -m femuralabs.toolkit.cli --shape 2 3 4 --spacing 3 1 1 --out output

Test the Compose network — services reach each other by name:

    docker compose up -d
    docker compose exec web python -c "import urllib.request; print(urllib.request.urlopen('http://api:8000/health').read())"
    docker compose down

Expected: `b'{"status": "ok"}'` — `web` reached `api` by service name, not
by IP. The service name only resolves on the Compose network; from the
workstation, use the published ports.

Common failures:

- `no configuration file provided: not found` — the terminal is not in the
  folder holding `docker-compose.yml`.
- `port is already allocated` — another program holds 8000 or 8080.
  `docker compose ps` shows leftovers; `docker compose down` removes them.


## Running the geometry service

Starts a small HTTP service that answers two JSON routes. No Docker needed.

    PYTHONPATH=src python -m femuralabs.toolkit.service.serve
    # prints: serving on 0.0.0.0:8000

In a second terminal:

    curl http://localhost:8000/health
    curl http://localhost:8000/info
    curl -i http://localhost:8000/missing

Expected:

    {"status": "ok"}
    {"shape": [4, 6, 6], "spacing": [2.0, 1.0, 1.0], "dtype": "float32", "extent_mm": [8.0, 6.0, 6.0]}
    HTTP/1.0 404 Not Found
    {"error": "not found"}

Stop the server with `Ctrl+C`. The bind address must be `0.0.0.0`: if it is
`127.0.0.1`, `curl` on the workstation hangs or is refused.

Without `curl`, the demo script does the same three requests against a
random free port:

    PYTHONPATH=src python scripts/api_demo.py

The `/info` route can serve a written report instead of the computed
default. Set `REPORT_FOLDER` and put an `info.json` in that folder:

    PYTHONPATH=src python -m femuralabs.toolkit.cli --shape 2 3 4 --spacing 3 1 1 --out output
    REPORT_FOLDER=output PYTHONPATH=src python -m femuralabs.toolkit.service.serve
    # in a second terminal:
    curl http://localhost:8000/info

Without `REPORT_FOLDER`, or when the folder does not hold `info.json`,
`/info` falls back to the four-key geometry dictionary. Both cases exit
200 and are covered by `tests/test_routes.py`.


## Recording a flow diagram

Each change that alters the module flow gets a diagram in `docs/FLOW.md`.
The section is prepended above the marker `<!-- INSERT HERE -->`; old
sections are never edited or removed. The command is the same every time —
only `--slug`, `--title`, `--description` and the JSON spec change:

    python scripts/draw_flow.py \
      --slug <short-semantic-slug> \
      --title "<human-readable heading>" \
      --description "<2-4 sentences>" \
      --spec - <<'EOF'
    {
      "nodes": [ ... ],
      "edges": [ ... ]
    }
    EOF

Expected: two printed lines, `wrote docs/flow/<slug>.png` and
`prepended section '<slug>' to docs/FLOW.md`. Open `docs/FLOW.md` and
confirm the new section is at the top, above any older section, with the
`<img src="flow/<slug>.png" ...>` attribute **relative to `docs/`**.

`--slug` values are semantic (`write-info-out-flag`,
`mounts-readonly-data-writable-output`), never a chapter, block, session
or date reference. Node kinds map to colours: `module` (blue),
`script` (green), `cli` (yellow), `file` (white-dashed), `external` (grey).

Re-running with an existing `--slug` exits non-zero. To regenerate, delete
the section from `FLOW.md`, delete the PNG, and re-run.


## Adding a new stage

When a new command has been run successfully on the workstation and its
output verified, add a section to this file with four parts:

1. **What it does**, in one sentence.
2. **The commands**, as a code block, no prompts inside the block.
3. **The expected output**, as a code block, so the reader can diff.
4. **What a failure means**, as a list of common failure modes and their
   cause.

Do not add a command that has not been run and verified. An unrun command
is a guess dressed as documentation.

## Alignment angles on a synthetic limb

Two scalar functions, no I/O, no file required. Prints the HKA
deviation in degrees and the MAD in millimetres for four synthetic
limbs — a straight one, a varus bend, a valgus bend, and the
sprint-doc's small-bend example. All numbers are hand-computable in
under a minute, which is what makes this the D10 pass test.

    PYTHONPATH=src python -c "
    from femuralabs.toolkit.alignment import hka_deviation, mad, knee_error_to_angle_deg
    def show(name, H, K, A):
        print(f'{name}: hka={hka_deviation(H,K,A):+7.3f}  mad={mad(H,K,A):+7.3f}')
    show('straight R ', (-100,0,0), (-100,0,-420), (-100,0,-820))
    show('varus R    ', (-100,0,0), (-120,0,-420), (-100,0,-820))
    show('varus L    ', ( 100,0,0), ( 120,0,-420), ( 100,0,-820))
    show('valgus R   ', (-100,0,0), ( -80,0,-420), (-100,0,-820))
    print('error prop 2mm / 420mm:', knee_error_to_angle_deg(2, 420), 'deg')
    "

Expected:

    straight R : hka= +0.000  mad= +0.000
    varus R    : hka= +5.589  mad=+20.000
    varus L    : hka= +5.589  mad=+20.000
    valgus R   : hka= -5.589  mad=-20.000
    error prop 2mm / 420mm: 0.2727... deg

Read as: **varus on the right and varus on the left are the same
positive number**, because the side is detected from hip.x sign. If
varus R and varus L disagree in sign, the side detector is broken;
the test `test_bent_limb_varus_is_positive_both_sides` catches it.

Straight-limb zero is the baseline. Any non-zero there means a bug in
the signed-lateral calculation, not a rounding artefact.

`tests/test_alignment.py` pins all four numbers plus the helper. Run
`pytest tests/test_alignment.py -v` for the actual verification; the
command above is for inspection.

## Verifying a clean checkout

Proves that the files tracked by git are enough to reproduce the project.
Clones into a temporary folder, runs the test suite, runs the CLI, builds
the image, runs it, and checks the output. Cleans up the clone on exit.

From project root, with the virtual environment active:

    bash scripts/clean_check.sh

Expected: `pytest -q` passes, the four geometry lines are printed twice
(once from the host Python, once from inside the container), and the script
ends with:

    clean checkout: all checks passed

Run this before trusting any commit: a file that exists in your working
tree but was never committed is invisible here. That is the point.


## Writing a geometry result to a folder

The `--out` flag writes `info.json` inside the named folder. Uses the
synthetic-volume path from the CLI section, so no input file is needed:

    PYTHONPATH=src python -m femuralabs.toolkit.cli --shape 2 3 4 --spacing 3 1 1 --out output
    cat output/info.json

Expected:

    shape (z, y, x): (2, 3, 4)
    spacing (mm): (3.0, 1.0, 1.0)
    dtype: float32
    extent (mm): (6.0, 3.0, 4.0)
    wrote: output/info.json
    {"shape": [2, 3, 4], "spacing": [3.0, 1.0, 1.0], "dtype": "float32", "extent_mm": [6.0, 3.0, 4.0]}

The extent 6.0, 3.0, 4.0 is 2×3, 3×1, 4×1 — voxel count times voxel
spacing, checkable by hand.

Omitting `--out` prints the four lines and writes nothing. The folder is
created if missing and left unchanged if present.

`output/` and `data/` are both ignored by git; nothing under them is
committed.


## Combining the two reference segmentations

The dataset ships femur and tibia on two separate crop volumes. The
pipeline reads one multi-label NIfTI on the full-limb grid. This section
records the exact procedure that produced `combined_seg.nii` on case 01,
on 27 October 2026, in 3D Slicer 5.12.4. It takes about 15 minutes per
subject by hand; a Python script replaces most of it in a later task, and
the manual procedure stays as the reference for verifying the script's
output.

The segmentations to combine are:
- `...-Pelvis-Thighs_Reconstruction.seg.nrrd` (contains femur, hip,
  sacrum, patella).
- `...-Shanks-Feet_Segmentation.seg.nrrd` (contains tibia, fibula, and
  foot bones).

The full-limb volume is `SMIR.Lower_limb.051Y.F.CT.168_1/CT.168.nrrd`,
512 × 512 × 1637 voxels. Do **not** use the two crop volumes
(`...-Pelvis-Thighs.nrrd`, `...-Shanks-Feet.nrrd`) — they are smaller and
do not reach the ankle.

### Producing the thighs NIfTI

1. In 3D Slicer, `File → Add Data` and open
   `SMIR.Lower_limb.051Y.F.CT.168_1/CT.168.nrrd`. Confirm in
   `Modules → Volumes → Volume Information` that `Image Dimensions` reads
   512, 512, 1637.
2. `File → Add Data` and open
   `...-Pelvis-Thighs_Reconstruction.seg.nrrd`.
3. In `Modules → Segmentations`, set **Source volume** to
   `SMIR.Lower_limb_051Y.F.CT.168_1` (no suffix, the full volume).
4. Click the small icon immediately to the right of the Source volume
   dropdown (the one that opens a **"Segment geometry"** dialog). In that
   dialog, confirm:
   - Source geometry is `SMIR.Lower_limb_051Y.F.CT.168_1`.
   - Dimensions are 512, 512, 1637.
   - Spacing is 0.9765625, 0.9765625, 0.6997555.
   Click **OK**. This step resamples the segmentation onto the full-limb
   grid; without it the export produces a crop-sized file.
5. In the same Segmentations module, scroll to the **"Export to files"**
   section and expand it. Set:
   - **File format**: `NIFTI (.nii.gz)` or `NIFTI (.nii)` (both work;
     `.nii` is what SimpleITK reads without decompression).
   - **Destination folder**: any Windows-side folder.
   - The **File name** is not editable here — it is derived from the
     segmentation name. Click **Export**.
6. Slicer writes two files into the destination folder:
   - `SMIR.Lower_limb.051Y.F.CT.168-Pelvis-Thighs_Reconstruction.nii`
     (or `.nii.gz`).
   - `..._Reconstruction.labels.csv` (colour and name table).
7. Copy both files to the WSL side and rename:

    cp /mnt/c/Users/<you>/Downloads/.../SMIR.Lower_limb.051Y.F.CT.168-Pelvis-Thighs_Reconstruction.nii \
       ~/FemuraLabs/data/raw/case01/thighs_on_full.nii
    cp /mnt/c/Users/<you>/Downloads/.../SMIR.Lower_limb.051Y.F.CT.168-Pelvis-Thighs_Reconstruction.labels.csv \
       ~/FemuraLabs/data/raw/case01/thighs_on_full.labels.csv

### Producing the shanks NIfTI

Repeat the procedure above with
`...-Shanks-Feet_Segmentation.seg.nrrd` in place of the thighs file.
Save the result as `shanks_on_full.nii` and `shanks_on_full.labels.csv`.

### Verifying both files are on the full-limb grid

    cd ~/FemuraLabs
    python -c "import SimpleITK as sitk; \
      a = sitk.ReadImage('data/raw/case01/thighs_on_full.nii'); \
      b = sitk.ReadImage('data/raw/case01/shanks_on_full.nii'); \
      print('thighs:', a.GetSize(), a.GetSpacing()); \
      print('shanks:', b.GetSize(), b.GetSpacing())"

Expected output:

    thighs: (512, 512, 1637) (0.9765625, 0.9765625, 0.6997554898262024)
    shanks: (512, 512, 1637) (0.9765625, 0.9765625, 0.6997554898262024)

If either prints `(312, 205, 889)`, the "Segment geometry" dialog was not
applied to that file — go back to that file's step 4, click the icon,
confirm the full-limb dimensions, click OK, and re-export.

### Merging into one multi-label file

The two files are on the same grid, so voxel `(i, j, k)` in one is the
same physical point as voxel `(i, j, k)` in the other. The merge reads
each file, extracts femur and tibia by their source label values (see
`docs/data.md` for the exact mapping), and writes them into a new array
under labels 1–4.

    cd ~/FemuraLabs
    python - <<'PY'
    import numpy as np
    import SimpleITK as sitk

    thighs = sitk.ReadImage('data/raw/case01/thighs_on_full.nii')
    shanks = sitk.ReadImage('data/raw/case01/shanks_on_full.nii')
    t = sitk.GetArrayFromImage(thighs)
    s = sitk.GetArrayFromImage(shanks)

    # Source label values, from the .labels.csv files. See docs/data.md.
    merged = np.zeros_like(t, dtype=np.uint8)
    merged[t == 5] = 1   # femur_R
    merged[t == 6] = 2   # femur_L
    merged[s == 2] = 3   # tibia_R
    merged[s == 9] = 4   # tibia_L
    merged[s == 3] = 5   # fibula_R
    merged[s == 10] = 6  # fibula_L

    out = sitk.GetImageFromArray(merged)
    out.CopyInformation(thighs)
    sitk.WriteImage(out, 'data/raw/case01/combined_seg.nii')
    print('wrote', out.GetSize(), 'labels', np.unique(merged))
    PY

Expected:

    wrote (512, 512, 1637) labels [0 1 2 3 4 5 6]

`CopyInformation` is not optional. Without it, SimpleITK writes the new
array with default geometry (spacing 1 mm, origin 0), and every downstream
mesh would be 2 per cent the wrong size.

The output filename in the script (`combined_seg.nii`) is a free
choice. SimpleITK writes gzipped NIfTI if the path ends in `.nii.gz` and
uncompressed if it ends in `.nii`; the array contents are identical. Both
forms read back with `sitk.ReadImage` regardless of their extension,
because SimpleITK detects the format from the file signature.

### Verifying the merged file

    python -c "import numpy as np, SimpleITK as sitk; \
      im = sitk.ReadImage('data/raw/case01/combined_seg.nii'); \
      arr = sitk.GetArrayFromImage(im); \
      print(im.GetSize(), im.GetSpacing()); \
      print('labels:', np.unique(arr)); \
      print('voxels:', {int(v): int((arr == v).sum()) for v in np.unique(arr)})"

Expected: `(512, 512, 1637)`, labels `[0 1 2 3 4 5 6]`, and non-zero
counts at every label 1–6 with background (0) dominating. Femurs and
tibias are in the millions of voxels; fibulas are ~77,000 voxels each
(thinner bones). If any of 1–6 is zero, the merge script matched no
voxels for that bone — check the source label value for that row
against `docs/data.md` before touching anything else.

### If the export produces a crop-sized file

Two working alternatives, in order of reliability:

**Fallback 1 — Export visible segments to binary labelmap.** Right-click
the **segmentation node** in the Data module (not the segment names inside
it, the top-level node whose name ends in `-Reconstruction` or
`-Segmentation`) and choose **"Export visible segments to binary
labelmap"** — the row immediately below "Export to file…". Slicer creates
a new volume node on the current source volume's grid. Right-click that
volume node → **Save** → format `NIFTI (.nii.gz)` or `NIFTI (.nii)`.

**Fallback 2 — BRAINS Resample.** `Modules → Resample Image (BRAINS)`.
Input Volume: the crop-sized labelmap. Reference Volume: the full-limb
volume `SMIR.Lower_limb_051Y.F.CT.168_1`. Interpolation Mode:
**NearestNeighbor** (mandatory for labels). Output Volume: a new node.
Apply, then save the output as NIfTI.

### What not to do

- Do not save as `.seg.nrrd` and try to read it in Python. SimpleITK reads
  it as a scalar array, not as label values.
- Do not skip `CopyInformation` in the merge script. The default geometry
  writes spacing 1 mm and downstream measurements become wrong by a
  factor of 0.98.
- Do not commit `combined_seg.nii`. It is derived data; `data/` is
  gitignored.

## Verifying a volume's geometry

Reads a file with `io_volume.load_volume`, prints the array shape and
the three geometry fields. The array shape is `(z, y, x)`; the three
geometry fields are `(x, y, z)`. Comparing the two lines is the fastest
way to confirm the file's geometry is not swapped.

    PYTHONPATH=src python -c "from femuralabs.toolkit.io_volume import load_volume; \
      v = load_volume('data/raw/case01/combined_seg.nii'); \
      print(v.array.shape, v.spacing, v.origin)"

Expected on case 01:

    (1637, 512, 512) (0.9765625, 0.9765625, 0.6997554898262024) (-249.51171875, -392.51171875, 119.69999694824219)

The array shape is the reverse of `GetSize()`'s `(512, 512, 1637)`. The
origin is negated in x and y relative to what Slicer shows because
SimpleITK reports in LPS and Slicer in RAS. Both are correct.

If the array shape comes back as `(512, 512, 1637)`, the file was read
through a tool that returns `(x, y, z)` order; do not call that a fix.
The `io_volume` contract is `(z, y, x)` for the array, and
`tests/test_io_volume.py::test_real_file_array_shape` pins it.

## Extracting per-bone masks from the combined segmentation

Reads `combined_seg.nii` and produces one `BoneMask` per bone, each
carrying a boolean mask, voxel count, volume in mL, and centroid in LPS
world coordinates.

    PYTHONPATH=src python -c "from femuralabs.toolkit.io_volume import load_volume; \
      from femuralabs.toolkit.masks import extract_masks; \
      m = extract_masks(load_volume('data/raw/case01/combined_seg.nii')); \
      [print(f'{b.name:<8} {b.voxel_count:>10}  {b.volume_ml:>8.1f} mL  x={b.centroid_world[0]:>9.1f} y={b.centroid_world[1]:>9.1f} z={b.centroid_world[2]:>9.1f}') for b in m.values()]"

Expected on case 01 (fibula values are new in D09; if your run differs
in the last two rows, that is the fibula, and the count should be
~77k for each side):

    femur_R      496845     331.6 mL  x=    -83.5 y=   -129.9 z=    870.7
    femur_L      452747     302.1 mL  x=    101.0 y=   -131.6 z=    894.4
    tibia_R      307340     205.1 mL  x=    -59.8 y=    -96.3 z=    493.8
    tibia_L      287692     192.0 mL  x=     87.5 y=    -99.3 z=    510.0
    fibula_R      77023     ~51.4 mL  x=    -75.9 y=    -96.6 z=    520.8
    fibula_L      77233     ~51.5 mL  x=     93.4 y=    -96.0 z=    536.3

Sanity checks on any new subject:

- Femur volumes in the 250-400 mL range for an adult cadaver; tibia
  150-250 mL. A value an order of magnitude off means spacing was read
  in the wrong axis order.
- `femur_L.x > femur_R.x` and `tibia_L.x > tibia_R.x`. In LPS the
  patient's left is +x; a swapped sign means the direction matrix was
  not applied or the (z, y, x) to (x, y, z) reorder was missed.
- Femurs have a higher z (proximal) than tibias (distal). They are
  separated by roughly 300-450 mm on a full lower-limb scan.

`tests/test_masks.py` pins all three checks against the real file, so
the command above is for inspection, not verification. Run
`pytest tests/test_masks.py -v` for the actual check.

## Producing an STL mesh from a mask

Reads the combined segmentation, extracts one bone, builds the mesh in
world millimetres, and writes an STL.

    PYTHONPATH=src python -c "from femuralabs.toolkit.io_volume import load_volume; \
      from femuralabs.toolkit.masks import extract_masks; \
      from femuralabs.toolkit.mesh import mask_to_mesh, save_stl; \
      v = load_volume('data/raw/case01/combined_seg.nii'); \
      m = extract_masks(v)['femur_R']; \
      verts, faces = mask_to_mesh(m.mask, v.spacing, v.origin, v.direction); \
      save_stl('data/raw/case01/femur_R.stl', verts, faces); \
      print(len(verts), 'verts', len(faces), 'faces', 'bbox', verts.min(0).round(1), verts.max(0).round(1))"

Expected on case 01:

    277167 verts 560642 faces bbox [-130.9 -170.3  658.2] [ -20.5  -76.6 1108.8]

Sanity checks on any new subject:

- `bbox` x should straddle the femur's centroid x. On this file the
  centroid is -83.5 and the bbox is [-130.9, -20.5]. Positive x means
  the direction matrix was dropped.
- `bbox` z spans about 400-500 mm on a femur at full-limb scale.
- The mesh opens in Slicer over the CT and sits on the bone, not at the
  origin.

**The ASCII STL is large** — 560,642 faces is roughly 110 MB. Do not
commit it; it lives in `data/` which is gitignored. Decimation in a later
task reduces the face count to 10-20 percent without visible loss at
clinical scales.

`tests/test_mesh.py::test_femur_mesh_is_near_mask_centroid` pins the
direction-matrix check by comparing the mesh centroid with the mask
centroid within 20 mm; run `pytest tests/test_mesh.py -v` for the
verification.

## Verifying a mesh

Reads the combined segmentation, extracts the right femur, builds the mesh,
and prints the edge counts and volume side by side.

    PYTHONPATH=src python - <<'PY'
    import numpy as np
    from femuralabs.toolkit.io_volume import load_volume
    from femuralabs.toolkit.masks import extract_masks
    from femuralabs.toolkit.mesh import mask_to_mesh, signed_volume, edge_incidence

    v = load_volume('data/raw/case01/combined_seg.nii')
    m = extract_masks(v)['femur_R']
    verts, faces = mask_to_mesh(m.mask, v.spacing, v.origin, v.direction)
    counts = edge_incidence(verts, faces)
    print('boundary edges:', counts['boundary'])
    print('manifold edges:', counts['manifold'])
    print('non-manifold edges:', counts['non_manifold'])
    print('mesh volume (mm^3):', round(abs(signed_volume(verts, faces)), 1))
    print('voxel volume (mm^3):', round(m.volume_ml * 1000, 1))
    PY

Expected on case 01:

    boundary edges: 0
    manifold edges: 840951
    non-manifold edges: 6
    mesh volume (mm^3): ~330000
    voxel volume (mm^3): 331600.0

Read the numbers as a diagnosis:

- **`boundary = 0`** — the mesh is closed. Every triangle edge belongs to
  another face. This is the property that volume, area, and boolean
  operations require.
- **`manifold`** — edges shared by exactly two faces; the vast majority.
- **`non-manifold`** — edges shared by three or more faces. skimage's
  marching cubes produces a handful at points where two surface patches
  touch along a line. Six out of ~840,000 on a real femur at 1 mm is
  normal, not a defect.
- **`mesh volume`** should be within a few percent of the voxel volume.
  Chamfering accounts for 5–10 percent; an order-of-magnitude difference
  means the direction matrix or the axis reorder was dropped.

If `boundary > 0`, the mesh is open. The usual cause is calling
`measure.marching_cubes` with `allow_degenerate=False` (which strips the
zero-area triangles that hold the surface closed at edge-touch points).
A second cause is a mask with interior holes; `scipy.ndimage.binary_fill_holes`
in `masks.py` fixes those.

If `mesh volume` is much less than the voxel volume, the same interior
holes are contributing negative volume from their inner surfaces. The
fix is the same `binary_fill_holes` call.

`tests/test_mesh.py` pins all three checks against the real file; run
`pytest tests/test_mesh.py -v` for the actual verification. The command
above is for inspection, not validation.

## Running the pipeline on one case

Reads a combined segmentation, extracts the four bones, meshes them,
writes four STLs and one JSON summary. Deterministic: same input, same
JSON.

    PYTHONPATH=src python scripts/pipeline_demo.py \
      --case data/raw/case01/combined_seg.nii \
      --out output/case01

Expected (vertex counts approximate; fibula rows are new in D09 and
will print with smaller vert counts than the long bones):

    wrote output/case01/summary.json
      femur_R    277167 verts   331.60 mL
      femur_L     ~250k verts   302.10 mL
      tibia_R     ~150k verts   205.10 mL
      tibia_L     ~140k verts   192.00 mL
      fibula_R    ~40k verts    51.4 mL
      fibula_L    ~40k verts    51.5 mL

Then inspect the JSON:

    cat output/case01/summary.json

The `size` field is `[x, y, z]`, matching SimpleITK's `GetSize()`, not the
array's `(z, y, x)`. `bbox_mm` is `null` for an absent bone, not a point
at the origin. `output/` is gitignored; nothing here is committed.

Pass the `--name` flag to override the case name in the JSON if the case
file lives outside its own subject folder.

`tests/test_pipeline_demo.py` pins the schema and determinism on a
synthetic volume; run `pytest tests/test_pipeline_demo.py -v` for the
check.

## Loading hand-placed landmarks

Reads a Slicer `.mrk.json` and returns `{name: (x, y, z)}` in LPS
millimetres. The loader respects the file's `coordinateSystem` field:
RAS files are negated in x and y to give LPS; LPS files are returned
unchanged.

    PYTHONPATH=src python -c "from femuralabs.toolkit.landmark_io import load_landmarks; \
      h = load_landmarks('data/ref/landmarks_case01.mrk.json'); \
      [print(f'{k:<22}', tuple(round(v,1) for v in val)) for k, val in h.items()]"

Expected on case01 (verify sign of x: `_R` landmarks have negative x,
`_L` landmarks have positive x, in LPS):

    femoral_head_R         (-70.8, -148.1, 1084.5)
    femoral_head_L         (94.2, -156.3, 1100.0)
    knee_centre_R          (-71.2, -127.9, 663.3)
    knee_centre_L          (81.9, -114.0, 685.0)
    ankle_centre_R         (-52.4, -76.4, 305.2)
    ankle_centre_L         (90.5, -89.9, 320.6)

If any `_R` landmark has positive x, the left/right labels are swapped
in the file. Fix by swapping suffixes in the `.mrk.json` (see
`docs/landmarks.md` trap 2).

## Femoral head centre by sphere fit

Extracts the femur mesh, fits a sphere to the medial hemisphere of the
proximal region, prints the fit centre and residual. Compares against
the hand-placed reference.

    PYTHONPATH=src python -c "
    import numpy as np
    from femuralabs.toolkit.io_volume import load_volume
    from femuralabs.toolkit.masks import extract_masks
    from femuralabs.toolkit.mesh import mask_to_mesh
    from femuralabs.toolkit.landmarks import femoral_head_centre
    from femuralabs.toolkit.landmark_io import load_landmarks
    v = load_volume('data/raw/case01/combined_seg.nii')
    m = extract_masks(v); h = load_landmarks('data/ref/landmarks_case01.mrk.json')
    for side in ('R', 'L'):
        verts, _ = mask_to_mesh(m[f'femur_{side}'].mask, v.spacing, v.origin, v.direction)
        centre, radius, rms = femoral_head_centre(verts)
        ref = np.array(h[f'femoral_head_{side}'])
        print(f'femur_{side}: fit {centre.round(1)}, hand {ref.round(1)}, '
              f'error {np.linalg.norm(centre-ref):.2f} mm, '
              f'radius {radius:.1f} mm, rms {rms:.2f} mm')
    "

Expected on case01 with default `medial_window_mm=20`:

    femur_R: fit (-73.3, -145.4, 1085.2), hand (-70.8, -148.1, 1084.5), error 3.81 mm, radius 18.3 mm, rms ~1 mm
    femur_L: fit (92.5, -156.8, 1104.5), hand (94.2, -156.3, 1100.0), error 4.82 mm, radius 20.4 mm, rms ~1 mm

Both errors are inside the hand-placement repeat distance for the same
point (4.26 and 6.21 mm). The automatic fit is at the level of a second
human placer.

**Radius diagnostic.** An adult femoral head is 17–25 mm radius. A fit
that returns 30+ mm has picked up the trochanter alongside the head
and is not the head centre. If the fit returns an out-of-range radius,
the medial window is wrong for this subject; see
`docs/landmarks.md` ("Extending to case02 and case03") for the sweep
diagnostic.

`tests/test_landmarks.py` pins the radius range and the 10 mm error
threshold against the case01 hand reference. Run
`pytest tests/test_landmarks.py -v` for the check.

## Ankle centre by malleoli midpoint

Reads the tibia and fibula meshes, finds the plafond (the flat bottom
of the shinbone that sits on the ankle bone), and takes the midpoint
of the medial (tibia) and lateral (fibula) malleoli at that level.
Prints the fit centre, the hand reference, the error, and the three
intermediate values that decided the fit.

    PYTHONPATH=src python -c "
    import numpy as np
    from femuralabs.toolkit.io_volume import load_volume
    from femuralabs.toolkit.masks import extract_masks
    from femuralabs.toolkit.mesh import mask_to_mesh
    from femuralabs.toolkit.landmarks import ankle_centre
    from femuralabs.toolkit.landmark_io import load_landmarks
    v = load_volume('data/raw/case01/combined_seg.nii')
    m = extract_masks(v)
    h = load_landmarks('data/ref/landmarks_case01.mrk.json')
    for side in ('R', 'L'):
        tv, _ = mask_to_mesh(m[f'tibia_{side}'].mask, v.spacing, v.origin, v.direction)
        fv, _ = mask_to_mesh(m[f'fibula_{side}'].mask, v.spacing, v.origin, v.direction)
        centre, info = ankle_centre(tv, fv)
        ref = np.array(h[f'ankle_centre_{side}'])
        err = float(np.linalg.norm(centre - ref))
        print(f'ankle_centre_{side}: auto {centre.round(1)}, hand {ref.round(1)}, '
              f'error {err:.2f} mm, plafond_z {info[\"plafond_z\"]:.1f} mm, '
              f'medial_x {info[\"medial_x\"]:.1f}, lateral_x {info[\"lateral_x\"]:.1f}')
    "

Expected on case 01:

    ankle_centre_R: auto [-53.7 -79.4 307.7], hand [-52.4 -76.4 305.2], error 4.15 mm, plafond_z 307.7 mm, medial_x -28.3, lateral_x -79.1
    ankle_centre_L: auto [ 92.8 -89.7 324.1], hand [ 90.5 -89.9 320.6], error 4.14 mm, plafond_z 324.1 mm, medial_x 64.5, lateral_x 121.1

Both errors are about twice the hand-placement repeat distance for the
same landmark (1.97 mm on R; the L repeat is treated as ~2.0 mm, not
0.84, per `docs/conventions.md` Known limitations). That is close to
the hand reference, but *not* at the level of a second human placer —
weaker than the femoral head fit, which matched the hand repeat.

**Reading the diagnostic if a number looks wrong:**

- **`plafond_z` within 3 mm of the tibia bottom** → the mesh is
  truncated; the search window found the malleolar tip, not the
  plafond. Check the tibia mask covers the full bone.
- **`plafond_z` more than 30 mm above the tibia bottom** → the widest
  band is a metaphyseal flare, not the plafond. Check the mask for a
  spur or a fracture callus.
- **`medial_x` on the wrong side of `lateral_x`** → the R/L
  detection is confused. This is caught by an explicit assertion in
  `tests/test_landmarks.py`.
- **Error > 6 mm with all three intermediates sane** → the
  assumption "plafond centroid ≈ talar dome directly beneath it" is
  what to question. That is the trigger for adding talus (see
  `docs/landmarks.md`, ankle_centre, "Why no talus yet").

`tests/test_landmarks.py::test_ankle_centre_right_agrees_with_hand_placement`
and `..._left_agrees_with_hand_placement` pin the 6 mm threshold and the
medial-vs-lateral ordering. Run `pytest tests/test_landmarks.py -v` for
the verification; the command above is for inspection.